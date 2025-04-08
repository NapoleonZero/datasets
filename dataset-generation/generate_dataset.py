#!/usr/bin/env python3
import sys
import asyncio
import signal
import os

if len(sys.argv) < 3:
    print("Invalid syntax")
    print("usage: generate_dataset <file> <depth> [is_main_thread]")
    sys.exit(1)

POSITIONS = sys.argv[1]
DEPTH = sys.argv[2]
MAIN_THREAD = False
if len(sys.argv) >= 4:
    MAIN_THREAD = sys.argv[3].lower() in ("true", "1", "yes")

ENGINE = "../NapoleonPP"
try:
    COLS = os.get_terminal_size().columns
except OSError:
    COLS = 80

engine_proc = None

def progress(p):
    progress_str = f" {p}%\r"
    num_bars = int((COLS * p / 100) - len(progress_str))
    if num_bars < 0:
        num_bars = 0
    bar = "█" * (num_bars + 1)
    sys.stdout.write(bar + progress_str)
    sys.stdout.flush()

async def read_line_with_timeout(proc, timeout):
    """Asynchronously read a line from proc.stdout with a timeout."""
    try:
        # proc.stdout.readline() returns bytes.
        line = await asyncio.wait_for(proc.stdout.readline(), timeout=timeout)
        if line:
            return line.decode().strip()
        return None
    except asyncio.TimeoutError:
        return None

async def send_command(proc, command):
    """Send a command to the engine process."""
    try:
        proc.stdin.write((command + "\n").encode())
        await proc.stdin.drain()
    except Exception as e:
        print("Failed to send command:", e)
        await restart_engine()

async def start_engine():
    """Start the engine subprocess and initialize it."""
    global engine_proc
    try:
        engine_proc = await asyncio.create_subprocess_exec(
            ENGINE,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
    except Exception as e:
        print("Failed to start engine:", e)
        sys.exit(1)
    
    try:
        init_line = await asyncio.wait_for(engine_proc.stdout.readline(), timeout=5)
        if init_line:
            pass
            # print("Engine init output:", init_line.decode().strip())
        else:
            print("No initialization output from engine.")
    except asyncio.TimeoutError:
        print("Engine timed-out during initialization")
    
    await send_command(engine_proc, "setoption Record")
    print("Engine started.")

async def restart_engine():
    """Terminate and restart the engine subprocess."""
    global engine_proc
    print("Restoring failed engine process...")
    if engine_proc:
        try:
            engine_proc.terminate()
            await asyncio.wait_for(engine_proc.wait(), timeout=5)
        except asyncio.TimeoutError:
            engine_proc.kill()
            await engine_proc.wait()
        except Exception:
            print("Process already terminated, restarting...")
    await start_engine()
    print("Engine process restored.")

def setup_signal_handlers(loop):
    for signame in ['SIGINT']:
        loop.add_signal_handler(getattr(signal, signame),
                                lambda: asyncio.create_task(ctrl_c()))

async def ctrl_c():
    """Clean shutdown on SIGINT or SIGTERM."""
    print("\nStopping dataset generation...")
    if engine_proc:
        await send_command(engine_proc, "quit")
        try:
            await asyncio.wait_for(engine_proc.wait(), timeout=10)
        except asyncio.TimeoutError:
            engine_proc.kill()
            await engine_proc.wait()
        except Exception:
            pass
    sys.exit(0)

async def main():
    await start_engine()

    # Read all FEN lines from the positions file.
    try:
        with open(POSITIONS, "r") as f:
            fen_lines = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print("Error reading positions file:", e)
        sys.exit(1)
    
    total_lines = len(fen_lines)
    count = 1

    for fen in fen_lines:
        await send_command(engine_proc, f"position fen {fen}")
        # If the engine has exited, restart it.
        if engine_proc.returncode is not None:
            await restart_engine()
            await send_command(engine_proc, f"position fen {fen}")

        if MAIN_THREAD and count % 100 == 0:
            progress(int(100 * count / total_lines))
        
        await send_command(engine_proc, f"go depth {DEPTH}")
        line = await read_line_with_timeout(engine_proc, timeout=1.0)
        retries = 0
        while line is None and retries < 5:
            print(f"Sending go command again: {fen}")
            await send_command(engine_proc, f"go depth {DEPTH}")
            line = await read_line_with_timeout(engine_proc, timeout=1.0)
            retries += 1

        # Process engine responses.
        while line is not None:
            if line.startswith("bestmove"):
                break
            elif line.startswith("Position"):
                print(f"Process failed with fen: {line}")
                await restart_engine()
                break
            elif not line.startswith("info"):
                print(f"Unexpected output with position {fen}: {line}")
                break
            else:
                line = await read_line_with_timeout(engine_proc, timeout=5.0)
        count += 1

    await send_command(engine_proc, "quit")
    await engine_proc.wait()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    setup_signal_handlers(loop)
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()

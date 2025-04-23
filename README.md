# datasets
Holds datasets along with tools to build and process them

## Generation
- Download the dataset:
    `download_dataset.sh` -> will download lichess database of evaluated positions at `datasets/lichess...jsonl.zst`
- Decompress and preprocess the dataset:
    `dataset-generation/convert_lichess.dataset.py datasets/lichess...json.zst output.csv`
- Further preprocess the csv by converting the fen positions into bitboards:
    run Napoleon, then: `preprocess in <in_file> out <out_file>`
- Encode the dataset into a binary format:
    run `./pack_dataset.py -i <in_file> -o <out_file>`
    The script uses struct to pack the entries of the csv with format '>QQQQQQQQQQQQbbbe'

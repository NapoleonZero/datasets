{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {

  buildInputs = [
    pkgs.python3Packages.zstandard
    pkgs.python3Packages.numpy
  ];

}
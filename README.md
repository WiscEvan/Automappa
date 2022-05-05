# Automappa: An interactive interface for exploration of metagenomes

![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/WiscEvan/Automappa?label=latest)
[![Anaconda-Server Install Badge](https://anaconda.org/bioconda/automappa/badges/installer/conda.svg)](https://conda.anaconda.org/bioconda)
[![Anaconda-Server Platforms Badge](https://anaconda.org/bioconda/automappa/badges/platforms.svg)](https://anaconda.org/bioconda/automappa)
[![Anaconda-Server Downloads Badge](https://anaconda.org/bioconda/automappa/badges/downloads.svg)](https://anaconda.org/bioconda/automappa)

| Image Name           | Image Tag       | Status                                                                                                                                                                                                                |
|----------------------|-----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `evanrees/automappa` | `main`,`latest` | [![docker CI/CD](https://github.com/WiscEvan/Automappa/actions/workflows/docker.yml/badge.svg?branch=main "evanrees/automappa:main")](https://github.com/WiscEvan/Automappa/actions/workflows/docker.yml)                                       |
| `evanrees/automappa` | `develop`       | [![develop docker CI/CD](https://github.com/WiscEvan/Automappa/actions/workflows/docker.yml/badge.svg?branch=develop "evanrees/automappa:develop")](https://github.com/WiscEvan/Automappa/actions/workflows/docker.yml) |

![automappa_demo_920](https://user-images.githubusercontent.com/25933122/158899748-bf21c1fc-6f67-4fd8-af89-4e732fa2edcd.gif)

## Getting Started

- [Clone the Automappa Repo](#clone-the-repository)
- [Run `make build` using Makefile](#build-images-for-automappa-services)
- [Run `make up` using Makefile](#build-and-run-automappa-services)
- [Open the Automappa url](#navigate-to-automappa-page)
## Clone the repository

## Automappa testing setup/run commands

### clone the Automappa Repository

```bash
git clone -b home-tab https://github.com/WiscEvan/Automappa
```

### build images for automappa services

```bash
make build
```

### build and run automappa services

NOTE: you can skip `make build` if you’d like, as this command will build and pull any images not available.

```bash
make up
```

### Navigate to Automappa page

Once you see `automappa_web_1` running from the terminal logs, you should be able to navigate to <localhost:8050> 🥳

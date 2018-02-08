# Moulder

An open-source interactive forward 2D gravity modeller.

Written in Python, using PyQt5 as GUI library and
[Fatiando a Terra](www.fatiando.org) under the hood for gravity forward
modelling.

## Cloning the repo

In order to start using `Moulder` you need to clone this repo:

```
git clone https://www.github.com/fatiando/moulder
```

## Install dependencies

Download [Anaconda](https://www.anaconda.com/download/) (Python 2.7 version).

Install a `C` compiler, such as `gcc`.
Under Debian or Ubuntu based disto:

```
sudo apt-get install gcc
```

Then change the working directory to the cloned repo:

```
cd moulder
```
and create a `conda` environment with:
```
conda env create -f environment.yml
```

Once it's installed you can change to the recently created `moulder`
environment with:

```
source activate moulder
```

# Install

Install Moulder through `pip`:

```
pip install .
```

# Running

In order to run `Moulder`, just run:

```
moulder
```

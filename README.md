## Installation

### Prerequisite
* Install Anaconda (https://docs.anaconda.com/anaconda/install/index.html)


### Install LENASampler Web Application
* Download LENASampler Code
```
git clone https://github.com/lingchen42/LENASampler.git
```

* Install LENASampler on your local computer through terminal
```
# cd into the source code
cd LENASampler 

# create software enviroment for running LENASampler
conda create -n lena_sampler python=3.10.6
conda activate lena_sampler
pip install -r requirements.txt
```

### Run LENASampler on your local machine
```
# cd into the source code
cd LENASampler/ui
flask run --port 5001
```
Got to `http://127.0.0.1:5001` to use the LENASampler Web Application
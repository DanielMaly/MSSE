# Overview 

MSSE is a content-based similarity search engine and web application for audio similarity retrieval. It was written as a semestral project at the Czech Technical University in Prague. The application's main purpose is to allow quick prototyping and testing of different similarity measures and methods of retrieval.

# Usage

Python 3 is required. First, install the requirements:

```
pip install -r requirements.txt
```

Libsamplerate and its Python wrapper are recommended for efficient processing. Unfortunately, the official wrapper doesn't support Python 3: please install [this](https://github.com/gregorias/samplerate) fork.

To set up the application SQLite database and preprocess data files for retrieval, use the following commands:

```
python create_database.py
python preprocess.py engine_name dataset_name
```

The engine name can be any engine class name from the engine.py file. A reasonably fast and reliable engine is the MandelEllisEngine. Your reference files (the ones being searched through) should be placed in `webapp/data/[dataset_name]`. A good reference dataset is [GTZAN](http://marsyasweb.appspot.com/download/data_sets/). If unzipped into webapp/data/genres, the preprocessing command for the MandelEllis engine would then look like this:

```
python preprocess.py genres MandelEllisEngine
```

To launch the application, run `python webapp.py` and connect to it on port 8000. 

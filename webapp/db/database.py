from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///asse.db'
db = SQLAlchemy(app)


class EngineModel(db.Model):
    __tablename__ = 'engine_model'

    clazz = db.Column(db.String(100), primary_key=True)

    def __init__(self, clazz):
        self.clazz = clazz

    def __repr__(self):
        return '<Engine %r>' % self.clazz


class Dataset(db.Model):
    __tablename__ = 'dataset'

    name = db.Column(db.String(100), primary_key=True)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Dataset %r>' % self.name


class AudioTrack(db.Model):
    __tablename__ = 'audio_track'

    id = db.Column(db.Integer, db.Sequence('audio_track_id'), primary_key=True)
    name = db.Column(db.String(100))
    path = db.Column(db.String(500))

    dataset_name = db.Column(db.String(100), db.ForeignKey('dataset.name'))
    dataset = db.relationship("Dataset", backref=db.backref('tracks'))

    def __init__(self, name, path, dataset):
        self.name = name
        self.path = path
        self.dataset = dataset

    def __repr__(self):
        return '<AudioTrack %r>' % self.name


class TrackSignature(db.Model):
    __tablename__ = 'track_signature'

    id = db.Column(db.Integer, db.Sequence('track_signature_id'), primary_key=True)
    path = db.Column(db.String(500))

    engine_class = db.Column(db.String(100), db.ForeignKey('engine_model.clazz'))
    engine_model = db.relationship("EngineModel", backref=db.backref('signtures'))

    audio_track_id = db.Column(db.Integer, db.ForeignKey('audio_track.id'))
    audio_track = db.relationship("AudioTrack", backref=db.backref('signatures'))

    def __init__(self, path, engine_model, audio_track):
        self.path = path
        self.engine_model = engine_model
        self.audio_track = audio_track

    def __repr__(self):
        return '<TrackSignature engine: %r | track: %r>' % self.engine_class, self.audio_track.name

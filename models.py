from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class WeatherHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(50), nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    query_time = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<WeatherHistory {self.city} {self.temperature} {self.description} {self.query_time}>'

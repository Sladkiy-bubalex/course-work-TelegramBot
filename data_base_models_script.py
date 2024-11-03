import os
import sqlalchemy as sq
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class DefaultWords(Base):
    __tablename__ = "default_word"

    id = sq.Column(sq.Integer, primary_key=True)
    title = sq.Column(sq.VARCHAR(30), nullable=False)
    translate = sq.Column(sq.VARCHAR(30), nullable=False)

    def __str__(self):
        return f"({self.id}, {self.title}, {self.translate})"

    def __init__(self, title, translate):
        self.title = (title,)
        self.translate = translate


class User(Base):
    __tablename__ = "user"

    id = sq.Column(sq.Integer, primary_key=True)
    chat_id = sq.Column(sq.Integer, unique=True)
    step = sq.Column(sq.Integer, nullable=False)

    def __str__(self):
        return f"{self.id}, {self.chat_id}, {self.step}"


class UserWords(Base):
    __tablename__ = "user_words"

    id = sq.Column(sq.Integer, primary_key=True)
    title = sq.Column(sq.VARCHAR(30), unique=True, nullable=False)
    translate = sq.Column(sq.VARCHAR(30), nullable=False)
    delete_word = sq.Column(sq.BOOLEAN, nullable=False)
    user_id = sq.Column(sq.Integer, sq.ForeignKey(User.id), nullable=False)

    user = relationship(User, backref="user_words")

    def __str__(self):
        return f"{self.id}, {self.title}, {self.translate}, {self.delete_word}, {self.user_id}"


def create_table(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    os.environ["name_db"] = input("Название базы данных: ")
    os.environ["name_user_db"] = input("Имя пользователя базы данных: ")
    os.environ["password_db"] = input("Пароль от базы данных: ")

    DSN = f"postgresql://{os.environ['name_sql']}:{os.environ['password_sql']}@localhost:5432/{os.environ['name_database']}"
    engine = sq.create_engine(DSN)

    create_table(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    def insert_default_words():
        words = {
            "работа": "work",
            "учиться": "study",
            "яблоко": "apple",
            "компьютер": "computer",
            "кружка": "mug",
            "романтика": "romance",
            "логистика": "logictics",
            "ночь": "night",
            "дерево": "tree",
            "автобус": "bus",
        }
        for title, translate in words.items():
            word = DefaultWords(title=title, translate=translate)
            session.add(word)
            session.commit()

    insert_default_words()
    session.close()

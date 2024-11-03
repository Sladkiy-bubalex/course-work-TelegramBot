import os
import random
import sqlalchemy as sq
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker
from master.data_base_models_script import DefaultWords, User, UserWords


DSN = f"postgresql://{os.environ['name_sql']}:{os.environ['password_sql']}@localhost:5432/{os.environ['name_database']}"


engine = sq.create_engine(DSN)
Session = sessionmaker(bind=engine)
session = Session()


def words(chat_id: int, step: int) -> tuple:
    """
    Получение всех слов изучаемых слов.

    Параметры
    -----------
    chat_id: int\n
        Id чата с пользователем
    step: int\n
        Id набора слов в результирующем словаре (шаг пользователя)

    Возвращает
    -----------
    Кортеж слов ((русское слово, англ. перевод), [вариант 1, вариант 2, вариант 3])
    """

    word_dict = {}
    check_user = session.query(User.id).filter(User.chat_id == chat_id).first()
    query1 = (
        session.query(UserWords.title, UserWords.translate)
        .join(User)
        .filter(User.chat_id == chat_id, UserWords.delete_word == False)
    )
    subq = session.query(UserWords.title).filter(
        UserWords.user_id == check_user[0], UserWords.delete_word == True
    )
    query2 = session.query(DefaultWords.title, DefaultWords.translate).filter(
        DefaultWords.title.not_in(subq)
    )
    result = query1.union(query2)
    for key, values in enumerate(result):
        word_dict[key] = values
    options = [value[1] for key, value in word_dict.items() if key != step]
    random.shuffle(options)
    print(word_dict)
    try:
        return word_dict[step], options[:3]
    except KeyError:
        return None


def new_user_for_db(chat_id: int):
    """
    Передает id чата в БД.

    Параметры
    -----------
    chat_id: int\n
        Id чата с пользователем

    Возвращает
    -----------
    True при удачном добавлении
    None если юзер уже существует в БД
    """
    query = session.query(User.chat_id).filter(User.chat_id == chat_id).all()
    if query == []:
        user = User(chat_id=chat_id, step=1)
        session.add(user)
        session.commit()
        return True


def update_step_user_db(chat_id: int, step: int) -> None:
    """
    Обновляет шаг пользователя в БД.

    Параметры
    -----------
    chat_id: int\n
        Id чата с пользователем
    step: int\n
        Шаг пользователя
    """

    session.query(User).filter(User.chat_id == chat_id).update({"step": step})
    session.commit()


def select_step_user_db(chat_id: int):
    """
    Получение из БД шага пользователя.

    Параметры
    -----------
    chat_id: int\n
        Id чата с пользователем

    Возвращает
    -----------
    Шаг пользователя или None если шаг отсутствует
    """
    query = session.query(User.step).filter(User.chat_id == chat_id).first()
    if query is not None:
        return query[0]
    else:
        return None


def add_word_user(title: str, translate: str, chat_id: int):
    """
    Добавление слова пользователем.

    Параметры
    -----------
    title: list\n
        русское слово
    translate: str\n
        перевод слова
    chat_id: int\n
        Id чата с пользователем

    Возвращает
    -----------
    Количество изучаемых слов при удачно добавлении или False если слово уже существует в БД
    """

    check_user = session.query(User.id).filter(User.chat_id == chat_id).first()
    check_word1 = (
        session.query(UserWords)
        .filter(UserWords.title == title, UserWords.delete_word == False)
        .first()
    )
    check_word2 = (
        session.query(DefaultWords).filter(DefaultWords.title == title).first()
    )
    if check_word1 is not None or check_word2 is not None:
        return False
    else:
        word = UserWords(
            title=title.lower(),
            translate=translate.lower(),
            delete_word=False,
            user_id=check_user[0],
        )
        session.add(word)
        session.commit()
    query1 = (
        session.query(UserWords.title, UserWords.translate)
        .join(User)
        .filter(User.chat_id == chat_id, UserWords.delete_word == False)
    )
    subq = session.query(UserWords.title).filter(
        UserWords.user_id == check_user[0], UserWords.delete_word == True
    )
    query2 = session.query(DefaultWords.title, DefaultWords.translate).filter(
        DefaultWords.title.not_in(subq)
    )
    result = query1.union(query2)
    return result.count()


def delete_word_user(word: str, chat_id: int) -> bool:
    """
    Удаляет слово пользователя.

    Параметры
    -----------
    word: str\n
        Русское слово, которе необходимо удалить
    chat_id: int\n
        Id чата с пользователем

    Возвращает
    -----------
    True - если слово удалено, None - если такого слова нет в БД
    """

    check_user = session.query(User.id).filter(User.chat_id == chat_id).first()
    if check_user is not None:
        query1 = session.query(UserWords.title).filter(
            UserWords.title == word, UserWords.user_id == check_user[0]
        )
        query2 = session.query(DefaultWords.title).filter(DefaultWords.title == word)
        result = query1.union(query2)
        if result.all() == []:
            return None
        elif query1.first() is not None:
            session.query(UserWords).filter(
                UserWords.title == word, UserWords.user_id == check_user[0]
            ).update({"delete_word": True})
            session.commit()
            return True
        elif query2.first() is not None:
            query3 = (
                session.query(DefaultWords.title, DefaultWords.translate)
                .filter(DefaultWords.title == word)
                .all()
            )
            for title, translate in query3:
                user_word = UserWords(
                    title=title,
                    translate=translate,
                    delete_word=True,
                    user_id=check_user[0],
                )
                session.add(user_word)
                session.commit()
                return True

import os
import sys
from sqlalchemy.ext.declarative import *
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from sqlalchemy.orm.exc import NoResultFound

Base = declarative_base()


class Record(Base):
    """
    :Author:  河海哥
    :Create:  2021/10/15 8:24 上午
    :Blog:    https://blog.csdn.net/qq_41376740
    Copyright (c) 2021, 河海哥 Group All Rights Reserved.
    """

    __tablename__ = 'record'

    id = Column(INT, primary_key=True, autoincrement=True)
    total_lines = Column(INT)
    computing_time = Column(DATETIME)
    suffix = Column(String(20))
    boost_number = Column(INT)
    # for the purpose of discriminating whether the data is generated due to import
    # and the convenience of future statistics, 1=yes 0=no
    import_flag = Column(INT)
    # for exact statistics of one file or one directory
    file_path = Column(String)

    def __str__(self):
        return """
    total_lines: %s;
    computing_time: %s,
    suffix: %s,
    boost_number: %s,
    file_path: %s
    """ % (self.total_lines, self.computing_time, self.suffix, self.boost_number, self.file_path)


def get_file_line_count(absolute_file_path, *args):
    """
    count lines in one file

    Args:
        absolute_file_path: file path
        *args: eliminate lines contains keywords that we don't want to count

    Returns:
        object: total number of rows
    """
    lines = open(absolute_file_path, "r", encoding="UTF-8").readlines()
    count = 0
    for line in lines:
        if "\n" == line:
            continue
        # tuple is not empty
        if not args:
            flag = False
            for arg in args:
                # if one line contains some related arguments , ignore it.
                # Jump out of current outer loop and continue next
                if line.find(arg) != -1:
                    flag = True
                    break
            if flag is True:
                continue
        count = count + 1
    return count


def statistics(file_path, suffix):
    keywords = {
        "java": ["package", "import", "}"],
        "py": []
    }
    sum_count = 0
    args = keywords.get(suffix)

    if os.path.isdir(file_path):
        g = os.walk(file_path)
        for root, dirs, files in g:
            for file in files:
                # eliminate the 'venv' directory
                if suffix == "py" and root.find("venv") != -1:
                    continue
                if file.endswith(suffix) is False:
                    continue
                absolute_file_path = os.path.join(root, file)
                print("scan the file: %s" % absolute_file_path)
                count = get_file_line_count(absolute_file_path, args)
                sum_count += count

    if os.path.isfile(file_path):
        sum_count = get_file_line_count(file_path, args)
    return sum_count


def get_latest_record(now):
    # get the latest record from db by computing_time, suffix and file_path
    latest_record = session.query(Record) \
        .filter(Record.computing_time <= now) \
        .filter(Record.suffix == suffix) \
        .filter(Record.file_path == directory) \
        .order_by(Record.computing_time.desc()) \
        .limit(1).one()
    return latest_record


def main():
    now = datetime.now()
    print("welcome my baby ,time :%s" % now)

    # get latest record from db
    last_record = Record()
    try:
        last_record = get_latest_record(now=now)
    except NoResultFound:
        last_record.total_lines = 0

    # print(last_record.total_lines)
    if os.path.exists(directory) is False:
        print("Path does not exists")
    else:
        total_lines = statistics(directory, suffix)
        print("The total lines of this path is：%d" % total_lines)

        if total_lines > 0:
            boost_number = total_lines - last_record.total_lines
            new_record = Record(total_lines=total_lines, computing_time=now, suffix=suffix, boost_number=boost_number,
                                import_flag=import_flag, file_path=directory)
            session.add(new_record)
            print("The new record is %s" % new_record)
            print("Store the data into MySQL")
            session.commit()
            session.close()


if __name__ == "__main__":
    # read three arguments from terminal
    directory, suffix, import_flag = sys.argv[1:4]
    print("Create session from db")
    engine = create_engine("mysql+pymysql://root:root@localhost:3307/line_record")
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    main()
    print("hello")
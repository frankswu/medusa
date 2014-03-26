#include <iostream>
#include <transform_moc.h>

using namespace std;

Transform::Transform() {
    reply = "";
    db.setDatabaseName(QDir::homePath() + "/.medusa.cache");
    db.open();
    python = new QProcess(this);
}

Transform::~Transform() {
    delete python;
    db.close();
}

void Transform::readStandardOutput() {
    reply += python->readAllStandardOutput();
}

void Transform::readStandardError() {
    reply += python->readAllStandardError();
}

void Transform::pythonFinished(int exitCode, QProcess::ExitStatus) {
    this->exitCode = exitCode;

    if (exitCode == 0) {
        QSqlQuery query(db);
        query.prepare("UPDATE MedusaCache SET GenCode=? WHERE InFile=?");
        query.addBindValue(reply);
        query.addBindValue(path);
        query.exec();
    } else
        cerr << reply.toStdString() << endl;
}

bool Transform::transform(QString path, QString &code) {
    QStringList args;

    args << "transform.py" << path;
    this->path = path;

    QObject::connect(python,
                SIGNAL(finished(int, QProcess::ExitStatus)),
                this, SLOT(pythonFinished(int, QProcess::ExitStatus)));
    QObject::connect(python,
                SIGNAL(readyReadStandardError()),
                this, SLOT(readStandardError()));
    QObject::connect(python,
                SIGNAL(readyReadStandardOutput()),
                this, SLOT(readStandardOutput()));

    python->start("python", args);
    python->waitForFinished();
    code = reply;

    return exitCode ? false : true;
}
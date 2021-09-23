from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QIcon


def create_action(icon, action, shortcut, tip, conn, parent):
    new_action = QAction(QIcon(icon), action, parent)
    new_action.setShortcut(shortcut)
    new_action.setStatusTip(tip)
    new_action.triggered.connect(conn)
    return new_action


def format_time(msec):
    sec = int(msec / 1000)
    t = []
    t.append(int(sec % 60))
    minu = sec/60
    t.append(int(minu % 60))
    t.append(int(minu/60))
    t = t[::-1]
    time = [str(tt).zfill(2) for tt in t]
    return ':'.join(time) + "," + format(msec % 1000, '03d')


def str_to_ms(txt):
    elems = txt.split(",")
    if len(elems) != 2:
        return -1
    ms = int(elems[1])
    elems2 = elems[0].split(":")
    if len(elems2) != 3:
        return -1
    h = int(elems2[0])
    m = int(elems2[1])
    s = int(elems2[2])

    return ms + 1000 * (s + 60 * (m + 60 * h))


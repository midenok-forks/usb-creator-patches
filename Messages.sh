#! /usr/bin/env bash

NAME="usbcreator"
XGETTEXT="xgettext -ki18n --language=Python"
EXTRACTRC="extractrc"

$EXTRACTRC gui/$NAME-kde.ui > ./$NAME-kde.ui.py
$XGETTEXT $NAME-kde.ui.py $NAME/frontends/kde/*.py -o "$NAME.pot"

sed -e 's/charset=CHARSET/charset=UTF-8/g' -i "$NAME.pot"

if [ -d "po" ]; then
    if [ -f "po/$NAME.pot" ]; then
        echo "Merging $NAME.pot -> po/$NAME.pot ..."
        msgcat -o "po/tmp-$NAME.pot" "po/$NAME.pot" "$NAME.pot"
        mv "po/tmp-$NAME.pot" "po/$NAME.pot"
    else
        echo "Copying $NAME.pot -> po/$NAME.pot ..."
        cp "$NAME.pot" "po/$NAME.pot"
    fi
fi

rm -f "$NAME-kde.ui.py"
rm -f "$NAME.pot"

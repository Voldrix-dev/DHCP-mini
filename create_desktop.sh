#!/bin/bash

# Скрипт создания .desktop файлов для системы и рабочего стола
# Автоматически определяет DE (KDE/GNOME-Ubuntu) и настраивает запуск с привилегиями без терминала.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DESKTOP_DIR="$HOME/Desktop"
APPLICATIONS_DIR="$HOME/.local/share/applications"
DESKTOP_FILE_NAME="dhcp_server_gui.desktop"

# Убедимся, что папки существуют
mkdir -p "$DESKTOP_DIR"
mkdir -p "$APPLICATIONS_DIR"

# =========================================================
# Определяем метод запуска в зависимости от окружения
# =========================================================

# --- 1. KDE: ищем kdesu ---
KDESU_PATH=""
if [ -f "/usr/lib/kf6/kdesu" ]; then
    KDESU_PATH="/usr/lib/kf6/kdesu"
elif [ -f "/usr/lib/kf5/kdesu" ]; then
    KDESU_PATH="/usr/lib/kf5/kdesu"
elif which kdesu &>/dev/null; then
    KDESU_PATH="$(which kdesu)"
fi

if [ -n "$KDESU_PATH" ]; then
    # --- KDE: запуск через kdesu ---
    EXEC_CMD="$KDESU_PATH -c $SCRIPT_DIR/run_gui.sh"
    TERMINAL_VAL="false"
    echo "[KDE] Найден kdesu ($KDESU_PATH). Запуск будет без терминала."

elif which pkexec &>/dev/null; then
    # --- Ubuntu/GNOME: генерируем run_gui_pkexec.sh ---
    # pkexec очищает окружение, поэтому нам нужно зафиксировать переменные
    # дисплея прямо сейчас (от имени текущего пользователя) в отдельный скрипт,
    # который pkexec затем выполнит с правами root.

    echo "[GNOME/Ubuntu] pkexec найден. Считываем переменные дисплея текущей сессии..."

    # Считываем текущие значения от пользователя (не root)
    REAL_DISPLAY="${DISPLAY:-:0}"
    REAL_XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
    REAL_WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"

    # XAUTHORITY: берем переменную или ищем файл в XDG_RUNTIME_DIR
    if [ -n "$XAUTHORITY" ]; then
        REAL_XAUTHORITY="$XAUTHORITY"
    else
        # Ищем .mutter-Xwaylandauth.* в XDG_RUNTIME_DIR
        MUTTER_AUTH=$(find "$REAL_XDG_RUNTIME_DIR" -maxdepth 1 -name ".mutter-Xwaylandauth.*" 2>/dev/null | head -1)
        if [ -n "$MUTTER_AUTH" ]; then
            REAL_XAUTHORITY="$MUTTER_AUTH"
        else
            REAL_XAUTHORITY="$HOME/.Xauthority"
        fi
    fi

    echo "  DISPLAY=$REAL_DISPLAY"
    echo "  XAUTHORITY=$REAL_XAUTHORITY"
    echo "  XDG_RUNTIME_DIR=$REAL_XDG_RUNTIME_DIR"
    echo "  WAYLAND_DISPLAY=$REAL_WAYLAND_DISPLAY"

    # Генерируем скрипт-обёртку run_gui_pkexec.sh
    PKEXEC_WRAPPER="$SCRIPT_DIR/run_gui_pkexec.sh"
    cat > "$PKEXEC_WRAPPER" <<WRAPPER_EOF
#!/bin/bash

SCRIPT_DIR="\$(cd "\$(dirname "\$0")" && pwd)"

export DISPLAY=$REAL_DISPLAY
export XAUTHORITY=$REAL_XAUTHORITY
export XDG_RUNTIME_DIR=$REAL_XDG_RUNTIME_DIR
export WAYLAND_DISPLAY=$REAL_WAYLAND_DISPLAY

exec "\$SCRIPT_DIR/dhcpenv/bin/python" "\$SCRIPT_DIR/dhcp_gui.py"
WRAPPER_EOF

    chmod +x "$PKEXEC_WRAPPER"
    echo "  Создан: $PKEXEC_WRAPPER"

    # Desktop запустит pkexec с нашим скриптом-обёрткой
    EXEC_CMD="pkexec $PKEXEC_WRAPPER"
    TERMINAL_VAL="false"
    echo "[GNOME/Ubuntu] Запуск настроен: pkexec $PKEXEC_WRAPPER"

else
    # --- Резерв: запуск через терминал с sudo ---
    EXEC_CMD="$SCRIPT_DIR/run_gui.sh"
    TERMINAL_VAL="true"
    echo "[Резерв] kdesu и pkexec не найдены. Запуск через терминал с sudo."
fi

# =========================================================
# Создаём .desktop файл
# =========================================================
cat <<EOF > "$SCRIPT_DIR/$DESKTOP_FILE_NAME"
[Desktop Entry]
Version=1.0
Type=Application
Name=DHCP Server
Comment=Управление локальным DHCP-сервером
Exec=$EXEC_CMD
Icon=$SCRIPT_DIR/dhcp_2.svg
Terminal=$TERMINAL_VAL
Categories=Network;System;
StartupNotify=true
EOF

# Копируем на рабочий стол и в меню приложений
cp "$SCRIPT_DIR/$DESKTOP_FILE_NAME" "$DESKTOP_DIR/$DESKTOP_FILE_NAME"
cp "$SCRIPT_DIR/$DESKTOP_FILE_NAME" "$APPLICATIONS_DIR/$DESKTOP_FILE_NAME"

# Делаем исполняемыми
chmod +x "$DESKTOP_DIR/$DESKTOP_FILE_NAME"
chmod +x "$APPLICATIONS_DIR/$DESKTOP_FILE_NAME"
chmod +x "$SCRIPT_DIR/$DESKTOP_FILE_NAME"

echo ""
echo "Файлы ярлыков успешно созданы:"
echo "  Рабочий стол:     $DESKTOP_DIR/$DESKTOP_FILE_NAME"
echo "  Меню приложений:  $APPLICATIONS_DIR/$DESKTOP_FILE_NAME"
echo ""
echo "Примечание: На рабочем столе GNOME/Ubuntu нажмите правой кнопкой мыши по"
echo "ярлыку и выберите 'Разрешить запуск' (Allow Launching)."

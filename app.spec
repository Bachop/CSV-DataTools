# -*- mode: python ; coding: utf-8 -*-
# 打包使用的py文件和ico文件以相对路径引用

import sys
import os
from PyInstaller.utils.hooks import collect_all, collect_system_data_files

# 从版本配置文件中读取版本号
# 使用当前工作目录代替__file__
current_dir = os.getcwd()
sys.path.append(os.path.join(current_dir, 'py'))
from SETTINGS.version import __version__, app_name, icon_path

# 收集Matplotlib所需的所有文件
matplotlib_datas, matplotlib_binaries, hiddenimports = collect_all('matplotlib')

# 收集PyQt5平台插件
def get_qt5_paths():
    import PyQt5
    return os.path.join(os.path.dirname(PyQt5.__file__), "Qt5")

qt5_path = get_qt5_paths()
platforms_path = os.path.join(qt5_path, "plugins", "platforms")

# 收集所有必要数据
datas = [
    ('matplotlibrc', '.'),  # Matplotlib配置
    *collect_system_data_files('matplotlib', include_py_files=True),
]

# 添加PyQt5平台插件
if os.path.exists(platforms_path):
    for file in os.listdir(platforms_path):
        if file.endswith('.dll'):
            datas.append((os.path.join(platforms_path, file), 'platforms'))

# 只添加必要的py目录中的Python模块，而不是所有文件
# datas += [(os.path.join('py', f), 'py') for f in os.listdir('py') if f.endswith('.py')]

# 添加图标文件到打包数据中
if os.path.exists(icon_path):
    datas.append((icon_path, 'icon'))

block_cipher = None

a = Analysis(
    ['py/main.py'],  # 修改为正确的模块化入口文件
    pathex=['.', 'py'],  # 添加py目录到路径
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports + [
        'matplotlib.backends.backend_qt5agg',
        'numpy.core._multiarray_umath',
        'csv',
        'chardet',
        'encodings',
        'encodings.*',
        
        # 添加项目模块
        'main_window',
        'data_viewer',
        'editable_table',
        'plot_window',
        'data_convert',
        'encoding_dialog',
        'column_selection_dialog',
        'version'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest', 'doctest', 'pdb'],  # 排除不必要的模块
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path
)

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name=app_name)
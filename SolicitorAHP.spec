# -*- mode: python ; coding: utf-8 -*-
from kivy import kivy_data_dir
from kivy_deps import sdl2, glew
from kivy.tools.packaging import pyinstaller_hooks as hooks

block_cipher = None
kivy_deps_all = hooks.get_deps_all()
kivy_factory_modules = hooks.get_factory_modules()

hiddenimports = kivy_deps_all['hiddenimports'] + kivy_factory_modules


a = Analysis(['main.py'],
             pathex=[],
             binaries=[],
             datas=[("layout.kv", ".")],
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
             
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,  
          *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
          name='SolicitorAHP',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )

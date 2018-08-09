# -*- mode: python -*-

block_cipher = None


a = Analysis(['src\\compare_reports.py'],
             pathex=['C:\\Users\\aabgreener\\Desktop\\git\\Denso\\Compare_GPOs'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='compare_reports',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False , version='version.txt', icon='apple_icon.ico')

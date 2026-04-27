# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app_ui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src', 'src'),
        ('config', 'config'),
        # sv_ttk ships theme Tcl/PNG files that PyInstaller won't discover automatically
        ('.venv/Lib/site-packages/sv_ttk', 'sv_ttk'),
        # CTY country-data file needed for continent/DXCC lookups
        ('cty_wt.dat', '.'),
    ],
    hiddenimports=[
        'sv_ttk',
        'src.database.db_manager',
        'src.database.models',
        'src.services.log_import_service',
        'src.services.cross_check_service',
        'src.services.scoring_service',
        'src.services.ubn_report_generator',
        'src.services.callsign_lookup',
        'src.parsers.cabrillo',
        'src.core.rules.rules_engine',
        'src.core.validation.contact_validator',
        'sqlalchemy.dialects.sqlite',
        # openpyxl is imported dynamically inside export methods and is therefore
        # invisible to PyInstaller's static analysis.  List it and its runtime
        # dependency (et_xmlfile) explicitly so Excel export works in the bundle.
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.utils',
        'openpyxl.utils.dataframe',
        'et_xmlfile',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SA10M',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SA10M',
)

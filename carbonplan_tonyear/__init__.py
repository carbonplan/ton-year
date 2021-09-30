import pathlib

from intake import open_catalog

cat_dir = pathlib.Path(__file__)
cat_file = str(cat_dir.parent / "data/catalog.yaml")
cat = open_catalog(cat_file)

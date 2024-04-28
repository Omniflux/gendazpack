gendazpack
==========

``gendazpack`` is a DAZ Studio content package generator.

Supported Python versions
-------------------------

- Python 3.11+

Usage
-----

``gendazpack [-h] [-g GLOBAL_ID] [-u URL] [-p PREFIX] [-s SKU] [-I ID] [-S STORE] [-n NAME] [-t <TAGS ...>] [-a <AUTHORS ...>] [-d DESCRIPTION] [-i IMAGE] [-r README] [-v] content_location``

positional arguments:
  content_location          Content directory

options:
  -h, --help            show this help message and exit
  -g GLOBAL_ID, --global-id GLOBAL_ID
                        Product Global ID
  -u URL, --url URL     URL for product information
  -p PREFIX, --prefix PREFIX
                        Source Prefix
  -s SKU, --sku SKU     Product SKU
  -I ID, --id ID        Package ID
  -S STORE, --store STORE
                        Product Store
  -n NAME, --name NAME  Product [Part] Name
  -t <TAGS ...>, --tags <TAGS ...>
                        Tags
  -a <AUTHORS ...>, --authors <AUTHORS ...>
                        Authors
  -d DESCRIPTION, --description DESCRIPTION
                        Product Description
  -i IMAGE, --image IMAGE
                        Product Image
  -r README, --readme README
                        Product ReadMe
  -v, --verbose         enable verbose output


.. code:: 

    E:\> gendazpack --sku 000000 --name "My Product" E:\ContentToPackage

    E:\> gendazpack --prefix ROSITY --sku 000000 --store Renderosity --name "Some Product" --image E:\ProductImage.png --readme E:\ProductReadme.pdf  E:\ContentToPackage

    E:\> gendazpack --url https://www.renderosity.com/marketplace/products/000000/some-product E:\ContentToPackage

License
-------

This module is published under the MIT license.
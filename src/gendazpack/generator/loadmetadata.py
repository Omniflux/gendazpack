import warnings

from pathlib import Path

from lxml import etree

from .packagedata import AssetData, ObjectData, PackageData

def load_metadata(content_location: Path) -> PackageData:
	_SUPPORT_DIR = 'Runtime/Support'

	metadata_files: list[Path] = []
	package_data = PackageData()

	if (support_path := content_location / _SUPPORT_DIR).is_dir():
		for entry in support_path.iterdir():
			if entry.is_file() and entry.suffix == '.dsx':
				metadata_files.append(entry)

	if len(metadata_files) > 1:
		raise RuntimeError('Multiple metadata files not supported by this tool')
    
	if metadata_files:
		try:
			metadata = etree.parse(metadata_files[0])
		except Exception as e:
			warnings.warn(f'Invalid Metadata file: {e}', RuntimeWarning)
		else:
			for e in metadata.xpath('/ContentDBInstall/Products/Product'):
				package_data.name = e.attrib['VALUE']
				package_data.global_id = eGUID[0].attrib['VALUE'] if (eGUID := e.xpath('GlobalID')) else None
				package_data.store = eStore[0].attrib['VALUE'] if (eStore := e.xpath('StoreID')) else None
				package_data.sku = int(eToken[0].attrib['VALUE']) if (eToken := e.xpath('ProductToken')) else None
				package_data.description = eDescription[0].text if (eDescription := e.xpath('Description')) else None
				package_data.artists = [a.attrib['VALUE'] for a in e.xpath('Artists/Artist')]
				package_data.objects = set(ObjectData(o.attrib['VALUE'], o.attrib['REF']) for o in e.xpath('ObjectCompatibilities/ObjectCompatibility'))
				package_data.assets = {Path(a.attrib['VALUE']).as_posix(): AssetData(
					aDescription[0].text if (aDescription := a.xpath('Description')) else None,
					aContentType[0].attrib['VALUE'] if (aContentType := a.xpath('ContentType')) else None,
					aAudience[0].attrib['VALUE'] if (aAudience := a.xpath('Audience')) else None,
					[c.attrib['VALUE'] for c in a.xpath('Categories/Category[string-length(@VALUE) > 0]')],
					[c.attrib['VALUE'] for c in a.xpath('Compatibilities/Compatibility[string-length(@VALUE) > 0]')],
					aCompatibilityBase[0].attrib['VALUE'] if (aCompatibilityBase := a.xpath('CompatibilityBase')) else None,
					[t.attrib['VALUE'] for t in a.xpath('Tags/Tag[string-length(@VALUE) > 0]')],
					[u.attrib['VALUE'] for u in a.xpath('Userwords/Userword[string-length(@VALUE) > 0]')],
					aUserNotes[0].text if (aUserNotes := a.xpath('UserNotes')) else None
				) for a in e.xpath('Assets/Asset')}

		if ((img := metadata_files[0].with_suffix('.jpg')).exists() or
			(img := metadata_files[0].with_suffix('.png')).exists()):
			package_data.image = img

		if package_data.store == 'LOCAL USER':
			package_data.store = None

	return package_data
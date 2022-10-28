import setuptools

long_description = 'long desc'
try:
	with open("readme.md", "r", encoding="utf-8") as fh:
		long_description = fh.read()
except:
	pass

setuptools.setup(
	name="smartapi",
	version="1.0.0",
	author="Michael Rommel",
	author_email="michamaxe@gmail.com",
	description="An awesome smart api",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url="https://github.com/mrommel/SmartAPI",
	packages=setuptools.find_packages(),
	classifiers=[
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
	],
	python_requires='>=3.8',
)

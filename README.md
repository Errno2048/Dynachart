# Dynachart
 A chart overview generator and extractor for Dynamix and Dynamite (MUG / Rhythm Game).

## view.py

### Usage

```shell
python view.py [-s | --scale SCALE] [-S | --speed SPEED] 
               [-l | --page_limit LIMIT] [-b | --bar_span BAR_SPAN]
               [-E | --encoding ENC] [-v | --verbose]
               [file [file ...]]
```

- Scale

  The zoom factor for the output images. Recommended value: 0.4.

- Speed

  The display speed for the chart. Recommended value: 0.8.

- Page limit

  The maximum bars allowed to show per page. The value has to be an integer. Recommended value: 16.

- Bar span

  The amount of bars between two bar lines.  The value has to be an integer. Recommended value: 2.

- Encoding

  The encoding of source files. Default: utf8.

- Verbose

  Whether to print messages.

### Example

```shell
python view.py -v hemisphere.xml
```

To generate overview picture `hemisphere.png` for the chart `hemisphere.xml`.

## extract.py

The Dynamix extractor. Use `python extract.py --help` to show help.

## dynamite.py

The Dynamite list editor.

### list

```shell
python dynamite.py list source
```

To generate JSON file for Dynamite chart list. `source` is the path for Dynamite source folder (`/Android/data/tech.dynami.dynamite/files`).

### sort

```shell
python dynamite.py sort source target [-r | --rename]
```

To move files for each song into corresponding folder. `source` is the path for Dynamite source folder and `target` is the target folder, where the generated files are.

Add `--rename` to rename song IDs.

### import

```shell
python dynamite.py import source song_folder song_name
                   [-i | --id ID] [-a | --artist ARTIST]
                   [-c | --charter CHARTER] [-d | --desc DESC]
                   [-r | --ranked]
```

To import a song into Dynamite.

`song_folder` is the source folder of the song, in which the following files exist.

- A cover picture whose name starts with `cover`, `_cover` or `_ocover`.
- A preview audio file started with `preview` or `_preview`.
- Another audio file as the full song.
- XML charts ends with `_X.xml` or `_X_L.xml`, where `X` is the difficulty (`B` or `C`, `N`, `H`, `M` or `G`) and `L` is the level. For example, `Hemisphere_M_14.xml`.

`ID`, `ARTIST`, `CHARTER` and `DESC` stands for the song ID, the artist, the charter and description, respectively.

`--ranked` indicates that the song is ranked.

### remove

```shell
python dynamite.py remove source id [id ...]
```

To remove songs with specified IDs.

### merge

```shell
python dynamite.py merge target source [source ...]
```

To merge source directory into target directory. Charts with identical ID will not be copied.

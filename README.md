# Dynachart
 A chart overview generator for Dynamix and Dynamite (MUG / Rhythm Game).

#### Usage

```shell
python main.py [-s | --scale SCALE] [-S | --speed SPEED] 
               [-l | --page_limit LIMIT] [-b | --bar_span BAR_SPAN]
               [-E | --encoding ENC] [-v | --verbose]
               [file [file ...]]
```

- Scale

  The zoom factor for the output images. Recommended value: 0.4.

- Speed

  The display speed for the chart. Recommended value: 0.8.

- Page limit

  The maximum bars allowed to show per page. The value have to be an integer. Recommended value: 16.

- Bar span

  The amount of bars between two bar lines.  The value have to be an integer. Recommended value: 2.

- Encoding

  The encoding of source files. Default: utf8.

- Verbose

  Whether to print messages.


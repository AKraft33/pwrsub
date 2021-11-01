<h1 align="center">PWRsub</h1>
<h4 align="center">Subtitle Extraction & Styling for large libraries</h4>    

---

<h4 align="center"> GPL 3.0 </h4>

---

<h2 align="left"> Getting Started </h2>

This software is designed to extract and style subtitles from your .mkv video library. To help achieve this, there are three distinct modes you can choose to run this program in.

Extract Mode: 
$ python pwrsub.py extract file_path
* Example: python pwrsub.py "media/user/shows/Cool Show/subtitles"
* This mode will extract all subtitles from .mkv files in file_path and put them into a folder named PWRsub_Exctact.
* IMPORTANT: use quotes to surround your file path if that file path contains spaces

Style Mode:
$ python pwrsub.py style master_file child_file
* Example: python pwrsub.py media/user/shows/master/subs.ass "media/user/shows/Cool Show/subtitles"
* This mode will take all of the styles applied to master_file and apply them to child_file
* Only supports .ass file format as .srt and .pgs do not support styles
* IMPORTANT: use quotes to surround your file path if that file path contains spaces

Extract & Style Mode:
$ python pwrsub.py extract_style file_path "font:Fira Sans Compressed"
* Example: python pwrsub.py extract_style "media/user/shows/Cool Show/subtitles" "font:Fira Sans Compressed" "bold:-1"
* Takes a directory and a list of style changes from CLI and modifies the subtitles with the listed style changes
* Only supports .ass file format as .srt and .pgs do not support styles
* Only a small number of style changes are supported, more can be added. If the style change you want is not supported, open an issue.
---

<h2 align="left"> Dependencies </h2>

<a href="https://mkvtoolnix.download/doc/mkvmerge.html"> MKVMerge </a> is needed to do extract the subtitles from the files

<A href="https://pypi.org/project/halo/"> Halo </a> is used for the in progress indicator

<A href="https://pypi.org/project/anitopy/"> Anitopy </a> is used to parse file names in order to group the correct files together for muxing 

---

<h2 align="left"> Tips </h2>

Use <a href="https://aegisub.en.uptodown.com/windows"> Aegis Subs </a> (Windows/Linux) to manually edit the styles of extracted subtitles to your liking then push those changes from a master file to the rest of the subtitles.

Look for subtitles that have the following:
* are in .ass format
* Actors correctly listed
* Multiple styles for different parts of the show

Avoid subtitles that have the following:
* Only one style for the entire subtitle
* Have custom styling done outside of standard styling
    - Standard styling is a style format applied to lines of dialogue that belong to that style
    - Non-Standard styling is styling that is applied directly to lines of dialogue and not through a style format
* Ideally, subtitles should NOT have dialogue lines belonging to no style
---
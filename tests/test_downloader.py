from yt_downloader_gui.core.models import QueueItem
from yt_downloader_gui.core.downloader import build_args


def _item(**kwargs) -> QueueItem:
    return QueueItem(url="https://example.com/watch?v=abc", **kwargs)


def test_mp4_args():
    args = build_args(_item(fmt="mp4"), output_dir="")
    assert args == ["yt-dlp", "-f", "best", "https://example.com/watch?v=abc"]


def test_mp3_args():
    args = build_args(_item(fmt="mp3"), output_dir="")
    assert args == [
        "yt-dlp", "-f", "bestaudio",
        "--extract-audio", "--audio-format", "mp3", "--audio-quality", "0",
        "https://example.com/watch?v=abc",
    ]


def test_mp3_with_audio_lang():
    args = build_args(_item(fmt="mp3", audio_lang="ja"), output_dir="")
    assert "-f" in args
    assert "bestaudio[lang=ja]" in args


def test_mkv_args():
    args = build_args(_item(fmt="mkv"), output_dir="")
    assert "--merge-output-format" in args
    assert "mkv" in args
    assert "bestvideo+bestaudio" in args


def test_4k_args():
    args = build_args(_item(fmt="4k"), output_dir="")
    assert "--merge-output-format" in args
    assert "mp4" in args
    assert any("height<=2160" in a for a in args)


def test_4k_no_av1_args():
    args = build_args(_item(fmt="4k-no-av1"), output_dir="")
    assert any("vcodec!=av01" in a for a in args)
    assert "--merge-output-format" in args
    assert "mkv" in args


def test_subs_args():
    args = build_args(_item(fmt="subs", sub_lang="fr"), output_dir="")
    assert "--write-subs" in args
    assert "--sub-lang" in args
    assert "fr" in args


def test_embed_subs_format_args():
    args = build_args(_item(fmt="embed-subs", sub_lang="en"), output_dir="")
    assert "--embed-subs" in args
    assert "--merge-output-format" in args
    assert "mp4" in args


def test_embed_subs_checkbox_on_mp4():
    args = build_args(_item(fmt="mp4", embed_subs=True, sub_lang="de"), output_dir="")
    assert "--embed-subs" in args
    assert "de" in args


def test_embed_subs_checkbox_not_duplicated_on_embed_subs_format():
    args = build_args(_item(fmt="embed-subs", embed_subs=True), output_dir="")
    assert args.count("--embed-subs") == 1


def test_output_dir_added():
    args = build_args(_item(fmt="mp4"), output_dir="C:/Videos")
    assert "-o" in args
    assert "C:/Videos/%(title)s.%(ext)s" in args


def test_url_is_last_arg():
    args = build_args(_item(fmt="mp4"), output_dir="")
    assert args[-1] == "https://example.com/watch?v=abc"

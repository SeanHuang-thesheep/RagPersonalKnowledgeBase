from denoise.cli import main


def test_cli_writes_output_file(make_pdf, tmp_path, capsys):
    pages = [
        [(50, 30, "ACME Confidential"), (50, 400, "First body line"), (180, 770, "1")],
        [(50, 30, "ACME Confidential"), (50, 400, "Second body line"), (180, 770, "2")],
    ]
    path = make_pdf(pages)
    out = str(tmp_path / "out.txt")
    rc = main([path, "-o", out])
    assert rc == 0
    with open(out, encoding="utf-8") as f:
        content = f.read()
    assert "First body line" in content
    assert "Second body line" in content
    assert "ACME Confidential" not in content


def test_cli_missing_file_returns_error(capsys):
    rc = main(["no_such_file.pdf"])
    assert rc == 1
    assert "Error" in capsys.readouterr().err


def test_cli_prints_to_stdout(make_pdf, capsys):
    path = make_pdf([[(50, 400, "Hello stdout")]])
    rc = main([path])
    assert rc == 0
    assert "Hello stdout" in capsys.readouterr().out


def test_cli_bad_output_path_returns_error(make_pdf, capsys):
    path = make_pdf([[(50, 400, "body")]])
    rc = main([path, "-o", "no_such_dir/out.txt"])
    assert rc == 1
    assert "Error" in capsys.readouterr().err


def test_cli_prints_summary_to_stderr(make_pdf, capsys):
    pages = [
        [(50, 30, "ACME Confidential"), (50, 400, "Body line"), (180, 770, "1")],
        [(50, 30, "ACME Confidential"), (50, 400, "More body"), (180, 770, "2")],
    ]
    path = make_pdf(pages)
    rc = main([path])
    assert rc == 0
    err = capsys.readouterr().err
    assert "Pages:" in err
    assert "blank:" in err
    assert "removed:" in err

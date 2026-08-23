"""Regression coverage for the inspect-matches CLI configuration backend."""


def test_inspect_matches_cli_config_backend():
    from vtool_ibeis import inspect_matches

    assert inspect_matches.kw.__name__ == 'kwconf'


def test_inspect_matches_cli_positional_args():
    from vtool_ibeis.inspect_matches import InspectMatchesCLI

    config = InspectMatchesCLI.cli(
        argv=['left-image.png', 'right-image.png'],
        data={},
        strict=True,
        verbose=False,
    )
    assert config.img1 == 'left-image.png'
    assert config.img2 == 'right-image.png'
    assert config.asdict()['img1'] == 'left-image.png'

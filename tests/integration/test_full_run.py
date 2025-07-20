import os
import sys
import subprocess

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


def test_full_analysis_run(tmp_path):
    output = tmp_path / "result.html"
    from src.config_parser import ConfigParser
    from src.analyzer import LocationAnalyzer

    parser = ConfigParser()
    cfg = parser.load_config('config')
    cfg['analysis']['grid_size'] = 2
    cfg['analysis']['max_radius'] = 5
    parser.validate_config(cfg)

    analyzer = LocationAnalyzer(cfg, cache_only=True)
    results = analyzer.run_analysis()
    html = analyzer._create_placeholder_html(results)
    output.write_text(html)
    assert output.exists()

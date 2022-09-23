from ra2ce.validation.validation_report import ValidationReport


class TestValidationReport:
    def test_init_validation_report(self):
        _report = ValidationReport()
        assert _report
        assert not _report._errors
        assert not _report._warns
        assert _report.is_valid()

    def test_error_validation_report(self):
        # 1. Define test data.
        _report = ValidationReport()
        _err_mssg = "Esse ea sint fugiat minim do consectetur officia nulla ullamco sunt proident."

        # 2. Run test.
        _report.error(_err_mssg)

        # 3. Verify expectations.
        assert not _report.is_valid()
        assert _err_mssg in _report._errors
        assert _err_mssg not in _report._warns

    def test_warn_validation_report(self):
        # 1. Define test data.
        _report = ValidationReport()
        _warn_mssg = "Duis occaecat cupidatat nisi ex elit elit esse et anim Lorem."

        # 2. Run test.
        _report.warn(_warn_mssg)

        # 3. Verify expectations.
        assert _report.is_valid()
        assert _warn_mssg in _report._warns
        assert _warn_mssg not in _report._errors

    def test_merge_validation_reports(self):
        # 1. Define test data.
        _report_source = ValidationReport()
        _report_target = ValidationReport()

        _source_warn_mssg = "Pariatur mollit pariatur enim laborum sunt ullamco cillum exercitation cupidatat eu Lorem duis eu dolore."
        _source_err_mssg = (
            "Deserunt reprehenderit culpa qui deserunt magna aliquip dolore pariatur."
        )
        _report_source.warn(_source_warn_mssg)
        _report_source.error(_source_err_mssg)

        _target_warn_mssg = "Quis id amet duis labore ea dolore officia aute labore esse cupidatat labore."
        _report_target.warn(_target_warn_mssg)

        assert _report_target.is_valid()
        assert not _report_source.is_valid()

        # 2. Run test.
        _report_target.merge(_report_source)

        # 3. Verify expectations.
        assert _report_source != _report_target

        assert not _report_target.is_valid()
        assert not _report_source.is_valid()

        assert _source_warn_mssg in _report_target._warns
        assert _source_err_mssg in _report_target._errors
        assert _target_warn_mssg not in _report_source._warns

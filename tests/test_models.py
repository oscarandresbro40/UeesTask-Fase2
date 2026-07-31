from app.models import SubmissionStatus, TaskStatus, UserRole


def test_domain_enums_preserve_documented_values():
    assert UserRole.TEACHER.value == "DOCENTE"
    assert UserRole.STUDENT.value == "ESTUDIANTE"
    assert TaskStatus.PUBLISHED.value == "PUBLICADA"
    assert SubmissionStatus.SUBMITTED.value == "ENVIADA"

import os

import quizgen.latex
import quizgen.pdf
import quizgen.util.dirent

import tests.base

class PdfConversionTest(tests.base.BaseTest):
    """
    Test PDF generation for quizzes in 'tests/quizzes/good' directory.
    A 'quiz.json' with an image question indicates a quiz that should be parsed and compiled to PDF.
    Tests covers local PDF generation, Docker PDF generation.
    """

    pass

def _find_all_quiz_json_files():
    """
    Find all quiz.json files in the 'tests/quizzes/good/' directory.
    """
    quiz_files = []
    
    # Walk through all subdirectories in the good quizzes directory
    for dirpath, _, filenames in os.walk(tests.base.GOOD_QUIZZES_DIR):
        if "quiz.json" in filenames:
            quiz_path = os.path.join(dirpath, "quiz.json")
            quiz_files.append(quiz_path)
    
    return quiz_files

def _add_pdf_tests():
    quiz_files = _find_all_quiz_json_files()
    
    if not quiz_files:
        raise ValueError(f"No quiz.json files found in '{tests.base.GOOD_QUIZZES_DIR}' or its subdirectories.")
    
    for quiz_path in quiz_files:
        _add_pdf_test(quiz_path)

def _add_pdf_test(path):
    base_test_name = os.path.basename(os.path.dirname(path))

    # Test local PDF generation.
    test_name = f"test_quiz_pdf_local_{base_test_name}"
    setattr(PdfConversionTest, test_name, _get_quiz_pdf_local_test_method(path))

    # Test Docker PDF generation.
    test_name = f"test_quiz_pdf_docker_{base_test_name}"
    setattr(PdfConversionTest, test_name, _get_quiz_pdf_docker_test_method(path))


def _get_quiz_pdf_local_test_method(path):
    """
    Get a test for generating a PDF locally.
    """
    def __method(self):
        quizgen.latex.set_pdflatex_use_docker(False)
        if (not quizgen.latex.is_available()):
            self.skipTest("pdflatex is not available")

        temp_dir = quizgen.util.dirent.get_temp_path(prefix = "quizgen_pdf_test_")
        quiz, variants, _ = quizgen.pdf.make_with_path(path, base_out_dir = temp_dir)

        for variant in variants:
            pdf_file = os.path.join(temp_dir, quiz.title, f"{variant.title}.pdf")
            self.assertTrue(os.path.exists(pdf_file), f"Local PDF '{pdf_file}' not generated")
            self.assertTrue(os.path.getsize(pdf_file) > 1000, f"Local PDF '{pdf_file}' is too small")

    return __method

def _get_quiz_pdf_docker_test_method(path):
    """
    Get a test for generating a PDF with Docker.
    """
    def __method(self):
        quizgen.latex.set_pdflatex_use_docker(True)
        if (not quizgen.latex.is_available()):
            self.skipTest("Docker is not available")

        temp_dir = quizgen.util.dirent.get_temp_path(prefix = "quizgen_pdf_test_")
        quiz, variants, _ = quizgen.pdf.make_with_path(path, base_out_dir = temp_dir)

        for variant in variants:
            pdf_file = os.path.join(temp_dir, quiz.title, f"{variant.title}.pdf")
            self.assertTrue(os.path.exists(pdf_file), f"Docker PDF '{pdf_file}' not generated")
            self.assertTrue(os.path.getsize(pdf_file) > 1000, f"Docker PDF '{pdf_file}' is too small")

    return __method

_add_pdf_tests()
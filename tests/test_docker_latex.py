import unittest
import os
import subprocess
import shutil
from quizgen.latex import compile
from quizgen.quiz import Quiz
from quizgen.pdf import make_with_path
from quizgen.util.json import loads, dump_path

class DockerTestBase(unittest.TestCase):
    DOCKER_IMAGE = "edulinq-quizgen-tex:latest"

    def setUp(self):
        self.test_dir = os.path.join("tests", "test_output")
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def check_docker_available(self):
        if subprocess.call(["docker", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
            self.skipTest("Docker is not installed or not running")

    def check_docker_image_exists(self):
        image_check = subprocess.run(["docker", "images", "-q", self.DOCKER_IMAGE], capture_output=True, text=True)
        if not image_check.stdout.strip():
            self.skipTest(f"Docker image '{self.DOCKER_IMAGE}' not found")

class TestDockerPdfConversion(DockerTestBase):
    def test_quiz_json_to_pdf(self):
        self.check_docker_available()
        self.check_docker_image_exists()

        quiz_json_string = '''
        {
            "title": "Docker Test Quiz",
            "description": "A test quiz for Docker PDF conversion",
            "questions": [
                {
                    "type": "multiple_choice",
                    "prompt": "What is 2 + 2?",
                    "options": [
                        {"text": "4", "correct": "true"},
                        {"text": "5", "correct": "false"}
                    ]
                }
            ]
        }
        '''
        quiz_json_path = os.path.join(self.test_dir, "test_quiz.json")
        dump_path(loads(quiz_json_string), quiz_json_path, indent=4)

        make_with_path(quiz_json_path, base_out_dir=self.test_dir, use_docker=True)
        pdf_file = os.path.join(self.test_dir, "Docker Test Quiz", "Docker Test Quiz.pdf")

        self.assertTrue(os.path.exists(pdf_file), "PDF file was not generated")
        self.assertGreater(os.path.getsize(pdf_file), 1000, "Generated PDF is too small, likely incomplete")

    def test_tex_to_pdf_with_docker(self):
        self.check_docker_available()
        self.check_docker_image_exists()

        tex_file_path = os.path.join(self.test_dir, "test_docker.tex")
        tex_content = r"""
        \documentclass{article}
        \usepackage[T1]{fontenc}
        \begin{document}
        \section{Test Section}
        This is a test document generated with Docker.
        \end{document}
        """
        with open(tex_file_path, 'w') as f:
            f.write(tex_content)

        compile(tex_file_path, use_docker=True)
        pdf_file = os.path.splitext(tex_file_path)[0] + '.pdf'

        self.assertTrue(os.path.exists(pdf_file), "PDF file was not generated")
        self.assertGreater(os.path.getsize(pdf_file), 1000, "Generated PDF is too small, likely incomplete")

if __name__ == '__main__':
    unittest.main()
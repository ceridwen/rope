import unittest
import rope.base.exceptions
import rope.base.project
from rope.refactor.change_signature import ChangeSignature
from rope.refactor import change_signature

from ropetest import testutils


class ChangeSignatureTest(unittest.TestCase):

    def setUp(self):
        super(ChangeSignatureTest, self).setUp()
        self.project_root = 'sample_project'
        testutils.remove_recursively(self.project_root)
        self.project = rope.base.project.Project(self.project_root)
        self.pycore = self.project.get_pycore()
        self.refactoring = self.project.get_pycore().get_refactoring()
        self.mod = self.pycore.create_module(self.project.get_root_folder(), 'mod')

    def tearDown(self):
        testutils.remove_recursively(self.project_root)
        super(ChangeSignatureTest, self).tearDown()

    def test_normalizing_parameters_for_trivial_case(self):
        code = 'def a_func():\n    pass\na_func()'
        self.mod.write(code)
        signature = ChangeSignature(self.pycore, self.mod,
                                    self.mod.read().index('a_func') + 1)
        signature.normalize().do()
        self.assertEquals(code, self.mod.read())

    def test_normalizing_parameters_for_trivial_case2(self):
        code = 'def a_func(param):\n    pass\na_func(2)'
        self.mod.write(code)
        signature = ChangeSignature(self.pycore, self.mod,
                                    self.mod.read().index('a_func') + 1)
        signature.normalize().do()
        self.assertEquals(code, self.mod.read())

    def test_normalizing_parameters_for_unneeded_keyword(self):
        self.mod.write('def a_func(param):\n    pass\na_func(param=1)')
        signature = ChangeSignature(self.pycore, self.mod,
                                    self.mod.read().index('a_func') + 1)
        signature.normalize().do()
        self.assertEquals('def a_func(param):\n    pass\na_func(1)', self.mod.read())

    def test_normalizing_parameters_for_unneeded_keyword_for_methods(self):
        self.mod.write('class A(object):\n    def a_func(self, param):\n        pass\n'
                       'a_var = A()\na_var.a_func(param=1)')
        signature = ChangeSignature(self.pycore, self.mod,
                                    self.mod.read().index('a_func') + 1)
        signature.normalize().do()
        self.assertEquals('class A(object):\n    def a_func(self, param):\n        pass\n'
                          'a_var = A()\na_var.a_func(1)', self.mod.read())

    def test_normalizing_parameters_for_unsorted_keyword(self):
        self.mod.write('def a_func(p1, p2):\n    pass\na_func(p2=2, p1=1)')
        signature = ChangeSignature(self.pycore, self.mod,
                                    self.mod.read().index('a_func') + 1)
        signature.normalize().do()
        self.assertEquals('def a_func(p1, p2):\n    pass\na_func(1, 2)', self.mod.read())

    @testutils.assert_raises(rope.base.exceptions.RefactoringException)
    def test_raising_exceptions_for_non_functions(self):
        self.mod.write('a_var = 10')
        signature = ChangeSignature(self.pycore, self.mod,
                                    self.mod.read().index('a_var') + 1)

    def test_normalizing_parameters_for_args_parameter(self):
        self.mod.write('def a_func(*arg):\n    pass\na_func(1, 2)\n')
        signature = ChangeSignature(self.pycore, self.mod,
                                    self.mod.read().index('a_func') + 1)
        signature.normalize().do()
        self.assertEquals('def a_func(*arg):\n    pass\na_func(1, 2)\n', self.mod.read())

    def test_normalizing_parameters_for_args_parameter_and_keywords(self):
        self.mod.write('def a_func(param, *args):\n    pass\na_func(*[1, 2, 3])\n')
        signature = ChangeSignature(self.pycore, self.mod,
                                    self.mod.read().index('a_func') + 1)
        signature.normalize().do()
        self.assertEquals('def a_func(param, *args):\n    pass\na_func(*[1, 2, 3])\n', self.mod.read())

    def test_normalizing_functions_from_other_modules(self):
        mod1 = self.pycore.create_module(self.project.get_root_folder(), 'mod1')
        mod1.write('def a_func(param):\n    pass\n')
        self.mod.write('import mod1\nmod1.a_func(param=1)\n')
        signature = ChangeSignature(self.pycore, mod1,
                                    mod1.read().index('a_func') + 1)
        signature.normalize().do()
        self.assertEquals('import mod1\nmod1.a_func(1)\n', self.mod.read())

    def test_normalizing_parameters_for_keyword_parameters(self):
        self.mod.write('def a_func(p1, **kwds):\n    pass\na_func(p2=2, p1=1)\n')
        signature = ChangeSignature(self.pycore, self.mod,
                                    self.mod.read().index('a_func') + 1)
        signature.normalize().do()
        self.assertEquals('def a_func(p1, **kwds):\n    pass\na_func(1, p2=2)\n', self.mod.read())
    
    def test_removing_arguments(self):
        self.mod.write('def a_func(p1):\n    pass\na_func(1)\n')
        signature = ChangeSignature(self.pycore, self.mod,
                                    self.mod.read().index('a_func') + 1)
        signature.remove(0).do()
        self.assertEquals('def a_func():\n    pass\na_func()\n', self.mod.read())

    def test_removing_arguments_with_multiple_args(self):
        self.mod.write('def a_func(p1, p2):\n    pass\na_func(1, 2)\n')
        signature = ChangeSignature(self.pycore, self.mod,
                                    self.mod.read().index('a_func') + 1)
        signature.remove(0).do()
        self.assertEquals('def a_func(p2):\n    pass\na_func(2)\n', self.mod.read())

    def test_removing_arguments_passed_as_keywords(self):
        self.mod.write('def a_func(p1):\n    pass\na_func(p1=1)\n')
        signature = ChangeSignature(self.pycore, self.mod,
                                    self.mod.read().index('a_func') + 1)
        signature.remove(0).do()
        self.assertEquals('def a_func():\n    pass\na_func()\n', self.mod.read())

    def test_removing_arguments_with_defaults(self):
        self.mod.write('def a_func(p1=1):\n    pass\na_func(1)\n')
        signature = ChangeSignature(self.pycore, self.mod,
                                    self.mod.read().index('a_func') + 1)
        signature.remove(0).do()
        self.assertEquals('def a_func():\n    pass\na_func()\n', self.mod.read())

    def test_removing_arguments_star_args(self):
        self.mod.write('def a_func(p1, *args):\n    pass\na_func(1)\n')
        signature = ChangeSignature(self.pycore, self.mod,
                                    self.mod.read().index('a_func') + 1)
        signature.remove(1).do()
        self.assertEquals('def a_func(p1):\n    pass\na_func(1)\n', self.mod.read())

    def test_removing_keyword_arg(self):
        self.mod.write('def a_func(p1, **kwds):\n    pass\na_func(1)\n')
        signature = ChangeSignature(self.pycore, self.mod,
                                    self.mod.read().index('a_func') + 1)
        signature.remove(1).do()
        self.assertEquals('def a_func(p1):\n    pass\na_func(1)\n', self.mod.read())

    def test_removing_keyword_arg2(self):
        self.mod.write('def a_func(p1, *args, **kwds):\n    pass\na_func(1)\n')
        signature = ChangeSignature(self.pycore, self.mod,
                                    self.mod.read().index('a_func') + 1)
        signature.remove(2).do()
        self.assertEquals('def a_func(p1, *args):\n    pass\na_func(1)\n', self.mod.read())

    # XXX: What to do here?
    def xxx_test_removing_arguments_star_args2(self):
        self.mod.write('def a_func(p1, *args):\n    pass\na_func(2, 3, p1=1)\n')
        signature = ChangeSignature(self.pycore, self.mod,
                                    self.mod.read().index('a_func') + 1)
        signature.remove(1).do()
        self.assertEquals('def a_func(p1):\n    pass\na_func(p1=1)\n', self.mod.read())

    # XXX: What to do here?
    def xxx_test_removing_arguments_star_args3(self):
        self.mod.write('def a_func(p1, *args):\n    pass\na_func(*[1, 2, 3])\n')
        signature = ChangeSignature(self.pycore, self.mod,
                                    self.mod.read().index('a_func') + 1)
        signature.remove(1).do()
        self.assertEquals('def a_func(p1):\n    pass\na_func(*[1, 2, 3])\n',
                          self.mod.read())
    
    def test_adding_arguments_for_normal_args_changing_definition(self):
        self.mod.write('def a_func():\n    pass\n')
        signature = ChangeSignature(self.pycore, self.mod,
                                    self.mod.read().index('a_func') + 1)
        signature.add(0, 'p1').do()
        self.assertEquals('def a_func(p1):\n    pass\n',
                          self.mod.read())

    def test_adding_arguments_for_normal_args_changing_definition_with_defaults(self):
        self.mod.write('def a_func():\n    pass\na_func()\n')
        signature = ChangeSignature(self.pycore, self.mod,
                                    self.mod.read().index('a_func') + 1)
        signature.add(0, 'p1', 'None').do()
        self.assertEquals('def a_func(p1=None):\n    pass\na_func()\n',
                          self.mod.read())

    def test_adding_arguments_for_normal_args_changing_calls(self):
        self.mod.write('def a_func():\n    pass\na_func()\n')
        signature = ChangeSignature(self.pycore, self.mod,
                                    self.mod.read().index('a_func') + 1)
        signature.add(0, 'p1', 'None', '1').do()
        self.assertEquals('def a_func(p1=None):\n    pass\na_func(1)\n',
                          self.mod.read())

    def test_adding_arguments_for_normal_args_changing_calls_with_keywords(self):
        self.mod.write('def a_func(p1=0):\n    pass\na_func()\n')
        signature = ChangeSignature(self.pycore, self.mod,
                                    self.mod.read().index('a_func') + 1)
        signature.add(1, 'p2', '0', '1').do()
        self.assertEquals('def a_func(p1=0, p2=0):\n    pass\na_func(p2=1)\n',
                          self.mod.read())

    def test_adding_arguments_for_normal_args_changing_calls_with_no_value(self):
        self.mod.write('def a_func(p2=0):\n    pass\na_func(1)\n')
        signature = ChangeSignature(self.pycore, self.mod,
                                    self.mod.read().index('a_func') + 1)
        signature.add(0, 'p1', '0', None).do()
        self.assertEquals('def a_func(p1=0, p2=0):\n    pass\na_func(p2=1)\n',
                          self.mod.read())

    @testutils.assert_raises(rope.base.exceptions.RefactoringException)
    def test_adding_duplicate_parameter_and_raising_exceptions(self):
        self.mod.write('def a_func(p1):\n    pass\n')
        signature = ChangeSignature(self.pycore, self.mod,
                                    self.mod.read().index('a_func') + 1)
        signature.add(1, 'p1').do()

    def test_inlining_default_arguments(self):
        self.mod.write('def a_func(p1=0):\n    pass\na_func()\n')
        signature = ChangeSignature(self.pycore, self.mod,
                                    self.mod.read().index('a_func') + 1)
        signature.inline_default(0).do()
        self.assertEquals('def a_func(p1=0):\n    pass\na_func(0)\n', self.mod.read())

    def test_inlining_default_arguments2(self):
        self.mod.write('def a_func(p1=0):\n    pass\na_func(1)\n')
        signature = ChangeSignature(self.pycore, self.mod,
                                    self.mod.read().index('a_func') + 1)
        signature.inline_default(0).do()
        self.assertEquals('def a_func(p1=0):\n    pass\na_func(1)\n', self.mod.read())

    def test_preserving_args_and_keywords_order(self):
        self.mod.write('def a_func(*args, **kwds):\n    pass\na_func(3, 1, 2, a=1, c=3, b=2)\n')
        signature = ChangeSignature(self.pycore, self.mod,
                                    self.mod.read().index('a_func') + 1)
        signature.normalize().do()
        self.assertEquals('def a_func(*args, **kwds):\n    pass\na_func(3, 1, 2, a=1, c=3, b=2)\n',
                          self.mod.read())
    
    def test_change_order_for_only_one_parameter(self):
        self.mod.write('def a_func(p1):\n    pass\na_func(1)\n')
        signature = ChangeSignature(self.pycore, self.mod,
                                    self.mod.read().index('a_func') + 1)
        signature.reorder([0]).do()
        self.assertEquals('def a_func(p1):\n    pass\na_func(1)\n',
                          self.mod.read())

    def test_change_order_for_two_parameter(self):
        self.mod.write('def a_func(p1, p2):\n    pass\na_func(1, 2)\n')
        signature = ChangeSignature(self.pycore, self.mod,
                                    self.mod.read().index('a_func') + 1)
        signature.reorder([1, 0]).do()
        self.assertEquals('def a_func(p2, p1):\n    pass\na_func(2, 1)\n',
                          self.mod.read())

    def test_reordering_multi_line_function_headers(self):
        self.mod.write('def a_func(p1,\n p2):\n    pass\na_func(1, 2)\n')
        signature = ChangeSignature(self.pycore, self.mod,
                                    self.mod.read().index('a_func') + 1)
        signature.reorder([1, 0]).do()
        self.assertEquals('def a_func(p2, p1):\n    pass\na_func(2, 1)\n',
                          self.mod.read())

    def test_changing_order_with_static_params(self):
        self.mod.write('def a_func(p1, p2=0, p3=0):\n    pass\na_func(1, 2)\n')
        signature = ChangeSignature(self.pycore, self.mod,
                                    self.mod.read().index('a_func') + 1)
        signature.reorder([0, 2, 1]).do()
        self.assertEquals('def a_func(p1, p3=0, p2=0):\n    pass\na_func(1, p2=2)\n',
                          self.mod.read())
    
    def test_doing_multiple_changes(self):
        changers = []
        self.mod.write('def a_func(p1):\n    pass\na_func(1)\n')
        changers.append(change_signature.ArgumentRemover(0))
        changers.append(change_signature.ArgumentAdder(0, 'p2', None, None))
        signature = ChangeSignature(self.pycore, self.mod,
                                    self.mod.read().index('a_func') + 1)
        signature.apply_changers(changers).do()
        self.assertEquals('def a_func(p2):\n    pass\na_func()\n', self.mod.read())

    def test_doing_multiple_changes2(self):
        changers = []
        self.mod.write('def a_func(p1, p2):\n    pass\na_func(p2=2)\n')
        changers.append(change_signature.ArgumentAdder(2, 'p3', None, '3'))
        changers.append(change_signature.ArgumentReorderer([1, 0, 2]))
        changers.append(change_signature.ArgumentRemover(1))
        signature = ChangeSignature(self.pycore, self.mod,
                                    self.mod.read().index('a_func') + 1)
        signature.apply_changers(changers).do()
        self.assertEquals('def a_func(p2, p3):\n    pass\na_func(2, 3)\n', self.mod.read())


if __name__ == '__main__':
    unittest.main()
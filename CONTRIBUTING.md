## Jazzband

[![Jazzband](https://jazzband.co/static/img/jazzband.svg)](https://jazzband.co/)

This is a [Jazzband](https://jazzband.co/) project. By contributing you agree to abide by the [Contributor Code of Conduct](https://jazzband.co/about/conduct) and follow the [guidelines](https://jazzband.co/about/guidelines).


## Coding style
This project follows the [HearthSim Styleguide](https://hearthsim.info/styleguide/).

In short:

1. Always use tabs. [Here](https://leclan.ch/tabs) is a short explanation why tabs are preferred.
2. Always use double quotes for strings, unless single quotes avoid unnecessary escapes.
3. When in doubt, [PEP8](https://www.python.org/dev/peps/pep-0008/). Follow its naming conventions.
4. Know when to make exceptions.

Also see: [How to name things in programming](http://www.slideshare.net/pirhilton/how-to-name-things-the-hardest-problem-in-programming)

Flake8 tests are available with `tox -e flake8`. Run them before you commit!


## Commits and Pull Requests
Keep the commit log as healthy as the code. It is one of the first places new contributors will look at the project.

1. No more than one change per commit. There should be no changes in a commit which are unrelated to its message.
2. Every commit should pass all tests on its own.
3. Follow [these conventions](http://chris.beams.io/posts/git-commit/) when writing the commit message

When filing a Pull Request, make sure it is rebased on top of most recent master.
If you need to modify it or amend it in some way, you should always appropriately
[fixup](https://help.github.com/articles/about-git-rebase/) the issues in git and force-push your changes to your fork.

Also see: [Github Help: Using Pull Requests](https://help.github.com/articles/using-pull-requests/)

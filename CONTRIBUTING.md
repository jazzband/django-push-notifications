## Code of Conduct

By contributing to django-push-notifications, you agree to abide by the
[Django Commons Code of Conduct](CODE_OF_CONDUCT.md).


## Documentation

Documentation is built with Sphinx. From the repository root, using Python 3.12 or newer:

```bash
python -m pip install -r docs/requirements.txt
python -m sphinx -W --keep-going -b html docs docs/_build/html
```

Open `docs/_build/html/index.html` to preview the documentation. The usage guide
includes `README.rst`, so update the README for installation, settings, and usage
changes. Provider guides live in `docs/FCM.rst`, `docs/APNS.rst`, and
`docs/WebPush.rst`.

Read the Docs uses the build configuration in `.readthedocs.yaml`.
To enable hosting, import this repository at <https://app.readthedocs.org/>,
select `master` as the default branch, and verify the first build succeeds.
For the Django Commons transfer, invite `djangocommons@gmail.com` as a maintainer
in the Read the Docs project's user settings. After the repository transfer,
update the project's repository URL and verify the GitHub integration still
triggers builds.


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

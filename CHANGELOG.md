# Changelog

## [0.2] - 2021-07-01

- Rename `CLInterface` to `Genbu`.
    + `name` and `description` are now optional arguments.
    + Change `Genbu.params` behavior.
        *   `params` are now inferred from the callback signature if not
            specified explicitly.
        *   If multiple `Param`s in the `params` list have the same `dest`,
            the one closer to the end of the list is used.
    + The CLI is now invoked by calling `Genbu.run`.
    + `Genbu.run` now reads inputs from `sys.argv[1:]` by default.
- Change `Param` attributes.
    + Rename `Param.name` to `Param.dest`
    + Rename `Param.parse` to `Param.parser`
    + Replace `Param.resolve` accumulator with `Param.aggregator`.
- Add `infer_params` function.

## [0.1] - 2021-06-23

- Initial release

[0.2]: https://github.com/lggruspe/genbu/releases/tag/v0.2
[0.1]: https://github.com/lggruspe/genbu/releases/tag/v0.1

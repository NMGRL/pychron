__author__ = "ross"

from pychron.core.progress import progress_loader


def progress_bind_records(ans):
    def func(xi, prog, i, n):
        xi.bind()
        if prog:
            if i == 0:
                prog.change_message("Loading")
            elif i == n - 1:
                prog.change_message("Finished")
            if prog and i % 25 == 0:
                prog.change_message("Loading {}".format(xi.record_id))
        return xi

    return progress_loader(ans, func, threshold=100, step=20)

import cProfile as profiler
import gc
import pstats
import time

def get_profile_stats(fn, *args, **kw):
    import cProfile, pstats
    prof = cProfile.Profile()

    # out = 'analysis_opt.prof'
    # prof = cProfile(out)
    prof.runcall(fn, *args, **kw)
    # prof.close()
    # stats = hotshot.stats.load(out)
    # stats.strip_dirs()

    stats = pstats.Stats(prof)
    return stats
    # stats.sort_stats('tottime')
    # stats.sort_stats('time', 'calls')
    # stats.print_stats(20)


def profile2(fn):
#     import cProfile, pstats, io
    def wrapper(*args, **kw):
        pr = profiler.Profile()
        pr.enable()
        fn(*args, **kw)
        pr.disable()
        pr.print_stats(sort='cumulative')
#         s = io.StringIO()
#         ps = pstats.Stats(pr, stream=s)
#         ps.print_results()
    return wrapper

def profile(fn):
    def wrapper(*args, **kw):
        p = "{}_profile.txt".format(fn.func_name())
        _elapsed, stat_loader, result = _profile(p, fn, *args, **kw)
        stats = stat_loader()
        stats.sort_stats('cumulative')
        stats.print_stats()
        # uncomment this to see who's calling what
        # stats.print_callers()
        return result
    return wrapper

def _profile(filename, fn, *args, **kw):
    load_stats = lambda: pstats.Stats(filename)
    gc.collect()

    began = time.time()
    profiler.runctx('result = fn(*args, **kw)', globals(), locals(),
                    filename=filename)
    ended = time.time()

    return ended - began, load_stats, locals()['result']

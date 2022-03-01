# ===============================================================================
# Copyright 2019 ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================
import corner as corner
from numpy.random import normal
from numpy import log, sqrt, pi, exp, hstack, percentile, argsort, linspace
import emcee
import matplotlib.pyplot as plt


def ln_prior(params):
    return 0


def norm_dist(val, mean, sigma):
    return (1.0 / sqrt(2.0 * pi * sigma**2)) * exp(
        -((val - mean) ** 2) / (2.0 * sigma**2)
    )


def ln_likelihood(param, vs, es):
    return


def sortedDataPlot(Ages, errors, ylims=[0, 1], **kwargs):
    # Load in some ages and errors, sort them, and then plot
    srtIdx = argsort(Ages)
    Ages = Ages[srtIdx]
    errors = errors[srtIdx]

    ys = linspace(ylims[0] * 1.1, ylims[1] * 0.9, len(Ages))
    plt.errorbar(Ages, ys, xerr=errors, fmt="o", **kwargs)


class BESTModeler:
    def setup(self):
        n = 20

        tu = 12.0
        dtu = tu * 0.1
        ts = tu + 2.0 * dtu
        dts = ts * 0.15

        tu_obs = normal(tu, dtu, n)
        ts_obs = normal(ts, dts, n)
        dtu_obs = tu_obs * 0.1
        dts_obs = ts_obs * 0.1

        self.tu_obs = tu_obs
        self.ts_obs = ts_obs
        self.dtu_obs = dtu_obs
        self.dts_obs = dts_obs

    def run(self):
        nburn = 50
        niter = 100
        nwalk = 100
        ndim = 2

        tuguess = self.tu_obs.mean()
        tsguess = self.ts_obs.mean()

        sample_tuguess = normal(tuguess, tuguess * 0.001, size=(nwalk, 1))
        sample_tsguess = normal(tsguess, tsguess * 0.001, size=(nwalk, 1))

        guesses = hstack((sample_tuguess, sample_tsguess))

        def proportional_ln_posterior(params):
            def ln_likelihood(ps):
                tu = log(norm_dist(ps[0], self.tu_obs, self.dtu_obs)).sum()
                ts = log(norm_dist(ps[1], self.ts_obs, self.dts_obs)).sum()
                return tu + ts

            return ln_prior(params) + ln_likelihood(params)

        sampler = emcee.EnsembleSampler(nwalk, ndim, proportional_ln_posterior)
        sampler.run_mcmc(guesses, nburn + niter)

        samples = sampler.chain[:, nburn].reshape((-1, ndim))
        names = [r"$t_u$", r"$t_s$"]
        # self.plot_walk(names, sampler, ndim, nwalk)
        self.plot_corner(names, samples)
        self.plot(samples)
        plt.show()

    def plot_corner(self, names, samples):
        corner.corner(samples, labels=names, quantiles=[0.05, 0.5, 0.95])

    def plot_walk(self, names, sampler, ndim, nwalk):
        f, axs = plt.subplots(ndim, 1, figsize=[7, 3])
        for i in range(ndim):
            for j in range(nwalk):
                axs[i].plot(sampler.chain[j, :, i], "-k", alpha=0.05)
            axs[i].set_ylabel(names[i], fontsize=14)

    def plot(self, samples):

        # f = plt.figure(figsize=[7, 3])
        plt.subplot(1, 2, 1)
        plt.hist(
            samples[:, 0],
            bins=50,
            histtype="stepfilled",
            normed=True,
            alpha=0.5,
            color="dodgerblue",
        )
        plt.hist(
            samples[:, 1],
            bins=50,
            histtype="stepfilled",
            normed=True,
            alpha=0.5,
            color="mediumseagreen",
        )

        ylims = plt.ylim()
        sortedDataPlot(
            self.tu_obs, self.dtu_obs, label=r"$t_u$", ylims=ylims, color="dodgerblue"
        )
        sortedDataPlot(
            self.ts_obs,
            self.dts_obs,
            label=r"$t_s$",
            ylims=ylims,
            color="mediumseagreen",
        )

        plt.gca().set_yticks([])  # a y-axis has no name
        plt.legend(fontsize="medium")
        plt.xlabel("Age")

        # To look at the modelled difference, we just difference the models
        plt.subplot(1, 2, 2)
        ageDiff = samples[:, 0] - samples[:, 1]
        ageDiffPercentiles = percentile(ageDiff, [2.5, 50, 97.5])
        resultsSummary = "{:.2f} ({:.2f} - {:.2f})".format(
            ageDiffPercentiles[1], ageDiffPercentiles[0], ageDiffPercentiles[2]
        )
        plt.hist(
            ageDiff,
            bins=50,
            histtype="stepfilled",
            normed=True,
            alpha=0.5,
            color="gray",
            label=resultsSummary,
        )
        ylim = plt.ylim()
        plt.plot([ageDiffPercentiles[0], ageDiffPercentiles[0]], ylim, "--k")
        plt.plot(
            [ageDiffPercentiles[2], ageDiffPercentiles[2]],
            ylim,
            "--k",
            label="95% credible interval",
        )
        plt.xlabel(r"$t_u - t_s$")
        plt.legend(fontsize="medium", loc="upper center")


if __name__ == "__main__":
    b = BESTModeler()
    b.setup()
    b.run()

# ============= EOF =============================================

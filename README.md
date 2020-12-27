# Jigglybluff's Final Submission: Ozzy Mozzy
Tournament Submission 
(Collaboration with A. Foo, a "MadMan" balancing on the fine line between genius and insanity...)

Note: Jigglybluff's bot performs precise tick-by-tick planning and execution, and therefore may require some minimal amount of compute resources to run properly (typically, an i5 or i7 core computer not running any other intensive processes should do the trick).
When running this bot, if you ever see the print out: "Skipped a Tick", it is likely performing suboptimally.

Known "bug": When running in --headless mode, apparently this bot skips a few ticks at the very start, which makes a difference as described above. We are not sure if this has a significant impact on the performance of this bot, but it would indeed perform suboptimally whenever "Skipped a Tick" happens.

"Troubleshooting": The bot is programmed to oscillate between 2 tiles when waiting. If the oscillation occurs over more than 2 tiles, it is likely that something has gone wrong (a de-sync likely happened). We suggest slowing down the tick rate (increasing tick_step in config.json) for "optimal experience".

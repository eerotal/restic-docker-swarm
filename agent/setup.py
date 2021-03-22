import setuptools

setuptools.setup(
    name="restic-docker-swarm-agent",
    packages=setuptools.find_packages(),
    python_requires='>=3.5',
    install_requires=[
        "docker>=4.2",
        "croniter>=1.0.8",
        "pause>=0.3"
    ],
    entry_points={}
)

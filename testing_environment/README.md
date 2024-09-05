# Testing Environment

We conduct extensive experiments on test tasks from the original [ALFWORLD](https://github.com/alfworld/alfworld) to evaluate the foundation models‘ performance and also to compare them with previous works. Therefore, we first need to install the ALFWORLD environment. Additionally, considering that running large-scale foundation models requires significant computational resources and many GPU servers are unable to run the Ai2-THOR visual simulator, MuEP adopts an HTTP testing framework. Specifically, we deploy the testing environment locally as the client, while the foundation models are deployed on the server side. The client primarily runs the text or multimodal testing environment, and the server side runs the corresponding foundation models for testing.




## Setup

First, we need to install the ALFWORLD testing environment by following [this guide](https://github.com/alfworld/alfworld).

After installing the ALFWORLD environment, the HTTP client configuration must be completed before running the test scripts. The `network_alfworld_client.py` corresponds to the multimodal testing client, while `network_textworld_client.py` corresponds to the pure text testing client. Next, we will take the multimodal testing setup as an example for configuration.

1.Configure the URL

Instantiate the `url` parameter in [network_alfworld_client.py L26](https://github.com/kanxueli/MuEP/blob/main/testing_environment/network_alfworld_client.py#L26) to specify the server's IP and PORT.

2.Select the Testing Environment (#Seen/#Unseen)

Depending on your needs, specify the testing environment by setting [network_alfworld_client.py L148](https://github.com/kanxueli/MuEP/blob/main/testing_environment/network_alfworld_client.py#L148). If you need to run tests in the #Seen scenario, select `seen_valid_path`. For the #Unseen scenario, select `unseen_valid_path`.

If you are conducting pure text-based testing, modify the `network_textworld_client.py` file. The configuration process is similar to steps 1 and 2.

3.Run the Testing Environment Client (Note: The client must be run after the server is started)

For multimodal testing, run the following script:

```bash
$ python network_alfworld_client.py
```
For text-based testing, run the following script:

```bash
$ python network_textworld_client.py
```



## Citations

**ALFWorld**

```
@inproceedings{ALFWorld20,
  title ={{ALFWorld: Aligning Text and Embodied
           Environments for Interactive Learning}},
  author={Mohit Shridhar and Xingdi Yuan and
          Marc-Alexandre C\^ot\'e and Yonatan Bisk and
          Adam Trischler and Matthew Hausknecht},
  booktitle = {Proceedings of the International Conference on Learning Representations (ICLR)},
  year = {2021},
  url = {https://arxiv.org/abs/2010.03768}
}
```



## License

- ALFWorld - MIT License
- TextWorld (Jericho) - GNU General Public License (GPL) v2.0
- Fast Downward - GNU General Public License (GPL) v3.0


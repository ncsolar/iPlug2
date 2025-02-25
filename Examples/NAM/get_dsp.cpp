#include <fstream>
#include <unordered_set>

#include "dsp.h"
#include "json.hpp"
#include "lstm.h"
#include "wavenet.h"
#include "numpy_util.h"
#include "HardCodedModel.h"


void verify_config_version(const std::string version)
{
  const std::unordered_set<std::string> supported_versions({"0.2.0", "0.2.1", "0.3.0", "0.3.1", "0.4.0"});
  if (supported_versions.find(version) == supported_versions.end())
    throw std::runtime_error("Unsupported config version");
}

std::unique_ptr<DSP> get_dsp(const std::filesystem::path dirname)
{
  const std::filesystem::path config_filename = dirname / std::filesystem::path("config.json");
  if (!std::filesystem::exists(config_filename))
    throw std::runtime_error("Config JSON doesn't exist!\n");
  std::ifstream i(config_filename);
  nlohmann::json j;
  i >> j;
  verify_config_version(j["version"]);

  auto architecture = j["architecture"];
  nlohmann::json config = j["config"];

  if (architecture == "Linear")
  {
    const int receptive_field = config["receptive_field"];
    const bool _bias = config["bias"];
    std::vector<float> params = numpy_util::load_to_vector(dirname / std::filesystem::path("weights.npy"));
    return std::make_unique<Linear>(receptive_field, _bias, params);
  }
  else if (architecture == "ConvNet")
  {
    const int channels = config["channels"];
    const bool batchnorm = config["batchnorm"];
    std::vector<int> dilations;
    for (int i = 0; i < config["dilations"].size(); i++)
      dilations.push_back(config["dilations"][i]);
    const std::string activation = config["activation"];
    std::vector<float> params = numpy_util::load_to_vector(dirname / std::filesystem::path("weights.npy"));
    return std::make_unique<convnet::ConvNet>(channels, dilations, batchnorm, activation, params);
  }
  else if (architecture == "CatLSTM")
  {
    const int num_layers = config["num_layers"];
    const int input_size = config["input_size"];
    const int hidden_size = config["hidden_size"];
    std::vector<float> params = numpy_util::load_to_vector(dirname / std::filesystem::path("weights.npy"));
    return std::make_unique<lstm::LSTM>(num_layers, input_size, hidden_size, params, config["parametric"]);
  }
  else if (architecture == "WaveNet" || architecture == "CatWaveNet")
  {
    std::vector<wavenet::LayerArrayParams> layer_array_params;
    for (int i = 0; i < config["layers"].size(); i++) {
      nlohmann::json layer_config = config["layers"][i];
      std::vector<int> dilations;
      for (int j = 0; j < layer_config["dilations"].size(); j++)
        dilations.push_back(layer_config["dilations"][j]);
      layer_array_params.push_back(
        wavenet::LayerArrayParams(
          layer_config["input_size"],
          layer_config["condition_size"],
          layer_config["head_size"],
          layer_config["channels"],
          layer_config["kernel_size"],
          dilations,
          layer_config["activation"],
          layer_config["gated"],
          layer_config["head_bias"]
        )
      );
    }
    const bool with_head = config["head"] == NULL;
    const float head_scale = config["head_scale"];
    std::vector<float> params = numpy_util::load_to_vector(dirname / std::filesystem::path("weights.npy"));
      
// Solution from:
//https://stackoverflow.com/questions/73874619/compilation-issue-on-mac-error-no-matching-constructor-for-initialization-of-w/73956681#73956681
    auto my_json = architecture == "CatWaveNet" ? config["parametric"] : nlohmann::json{};
    return std::make_unique<wavenet::WaveNet>(
          layer_array_params,
          head_scale,
          with_head,
          my_json,
          params
        );
  }
  else
  {
      throw std::runtime_error("Unrecognized architecture");
  }
}

std::unique_ptr<DSP> get_hard_dsp()
{
  // Values are defined in HardCodedModel.h
  verify_config_version(std::string(PYTHON_MODEL_VERSION));

  // Uncomment the line that corresponds to the model type that you're using.
  
  return std::make_unique<convnet::ConvNet>(CHANNELS, DILATIONS, BATCHNORM, ACTIVATION, PARAMS);
  //return std::make_unique<wavenet::WaveNet>(LAYER_ARRAY_PARAMS, HEAD_SCALE, WITH_HEAD, PARAMETRIC, PARAMS);
  //return std::make_unique<lstm::LSTM>(NUM_LAYERS, INPUT_SIZE, HIDDEN_SIZE, PARAMS, PARAMETRIC);
    
}

// Copyright 2020 ros2_control Development Team
// Copyright 2026 ludrol
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "orion_vi_hardware_interface/orion_vi_wheels.hpp"

#include <chrono>
#include <cmath>
#include <iomanip>
#include <limits>
#include <memory>
#include <sstream>
#include <string>
#include <vector>

#include <mqtt/async_client.h>

// #include "hardware_interface/types/hardware_interface_type_values.hpp"
#include "rclcpp/rclcpp.hpp"

const std::string MQTT_SERVER{"192.168.1.1"}; //rasberrka
const std::string CLIENT_ID{"ros_control_hardware_interface"}; //??
const std::string CMD_TOPIC{""}; //jak zrobić topiki dla wachaczy
const std::string TELEMETRY_TOPIC{""}; //ten czy inny plugin ros_control

const int QOS = 1;


namespace orion_vi_hardware_interface
{
hardware_interface::CallbackReturn OrionVIWheels::on_init(
  const hardware_interface::HardwareComponentInterfaceParams & params)
{
  // TODO
  // 


  // if (
  //   hardware_interface::SystemInterface::on_init(params) !=
  //   hardware_interface::CallbackReturn::SUCCESS)
  // {
  //   return hardware_interface::CallbackReturn::ERROR;
  // }


  // for (const hardware_interface::ComponentInfo & joint : info_.joints)
  // {
  //   // RRBotSystemPositionOnly has exactly one state and command interface on each joint
  //   if (joint.command_interfaces.size() != 1)
  //   {
  //     RCLCPP_FATAL(
  //       get_logger(), "Joint '%s' has %zu command interfaces found. 1 expected.",
  //       joint.name.c_str(), joint.command_interfaces.size());
  //     return hardware_interface::CallbackReturn::ERROR;
  //   }

  //   if (joint.command_interfaces[0].name != hardware_interface::HW_IF_POSITION)
  //   {
  //     RCLCPP_FATAL(
  //       get_logger(), "Joint '%s' have %s command interfaces found. '%s' expected.",
  //       joint.name.c_str(), joint.command_interfaces[0].name.c_str(),
  //       hardware_interface::HW_IF_POSITION);
  //     return hardware_interface::CallbackReturn::ERROR;
  //   }

  //   if (joint.state_interfaces.size() != 1)
  //   {
  //     RCLCPP_FATAL(
  //       get_logger(), "Joint '%s' has %zu state interface. 1 expected.", joint.name.c_str(),
  //       joint.state_interfaces.size());
  //     return hardware_interface::CallbackReturn::ERROR;
  //   }

  //   if (joint.state_interfaces[0].name != hardware_interface::HW_IF_POSITION)
  //   {
  //     RCLCPP_FATAL(
  //       get_logger(), "Joint '%s' have %s state interface. '%s' expected.", joint.name.c_str(),
  //       joint.state_interfaces[0].name.c_str(), hardware_interface::HW_IF_POSITION);
  //     return hardware_interface::CallbackReturn::ERROR;
  //   }
  // }
  RCLCPP_FATAL(get_logger(),"OrionVIWheels::on_init not implemented");
  return hardware_interface::CallbackReturn::ERROR;
  // return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn OrionVIWheels::on_configure(
  const rclcpp_lifecycle::State & /*previous_state*/)
{

  // this is the part where you connect to MQTT

  auto clientOptions = mqtt::create_options_builder()
                          // .server_uri(MQTT_SERVER)
                          .send_while_disconnected(true, true)
                          .max_buffered_messages(0)
                          .delete_oldest_messages(true)
                          // .restore_messeges(false)
                          .finalize();

  mqtt::async_client client(MQTT_SERVER,CLIENT_ID, clientOptions,NULL);

  auto connectionOptions = mqtt::connect_options_builder()
                    .clean_session()
                    .keep_alive_interval(std::chrono::seconds(5))
                    .automatic_reconnect(std::chrono::seconds(1), std::chrono::seconds(5))
                    .finalize();

  client.connect(connectionOptions);


  // // BEGIN: This part here is for exemplary purposes - Please do not copy to your production code
  // RCLCPP_INFO(get_logger(), "Configuring ...please wait...");

  // for (int i = 0; i < hw_start_sec_; i++)
  // {
  //   rclcpp::sleep_for(std::chrono::seconds(1));
  //   RCLCPP_INFO(get_logger(), "%.1f seconds left...", hw_start_sec_ - i);
  // }
  // // END: This part here is for exemplary purposes - Please do not copy to your production code

  // // reset values always when configuring hardware
  // for (const auto & [name, descr] : joint_state_interfaces_)
  // {
  //   set_state(name, 0.0);
  // }
  // for (const auto & [name, descr] : joint_command_interfaces_)
  // {
  //   set_command(name, 0.0);
  // }
  // RCLCPP_INFO(get_logger(), "Successfully configured!");
  RCLCPP_FATAL(get_logger(),"OrionVIWheels::on_configure not implemented");
  return hardware_interface::CallbackReturn::ERROR;
  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn OrionVIWheels::on_activate(
  const rclcpp_lifecycle::State & /*previous_state*/)
{

  //send command to power on the rockers - could be skipped for now


  // // BEGIN: This part here is for exemplary purposes - Please do not copy to your production code
  // RCLCPP_INFO(get_logger(), "Activating ...please wait...");

  // for (int i = 0; i < hw_start_sec_; i++)
  // {
  //   rclcpp::sleep_for(std::chrono::seconds(1));
  //   RCLCPP_INFO(get_logger(), "%.1f seconds left...", hw_start_sec_ - i);
  // }
  // // END: This part here is for exemplary purposes - Please do not copy to your production code

  // // command and state should be equal when starting
  // for (const auto & [name, descr] : joint_state_interfaces_)
  // {
  //   set_command(name, get_state(name));
  // }

  // RCLCPP_INFO(get_logger(), "Successfully activated!");
  RCLCPP_FATAL(get_logger(),"OrionVIWheels::on_activate not implemented");
  return hardware_interface::CallbackReturn::ERROR;
  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn OrionVIWheels::on_deactivate(
  const rclcpp_lifecycle::State & /*previous_state*/)
{
  // // BEGIN: This part here is for exemplary purposes - Please do not copy to your production code
  // RCLCPP_INFO(get_logger(), "Deactivating ...please wait...");

  // for (int i = 0; i < hw_stop_sec_; i++)
  // {
  //   rclcpp::sleep_for(std::chrono::seconds(1));
  //   RCLCPP_INFO(get_logger(), "%.1f seconds left...", hw_stop_sec_ - i);
  // }

  // RCLCPP_INFO(get_logger(), "Successfully deactivated!");
  // // END: This part here is for exemplary purposes - Please do not copy to your production code
  RCLCPP_FATAL(get_logger(),"OrionVIWheels::on_deactivate not implemented");
  return hardware_interface::CallbackReturn::ERROR;
  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::return_type OrionVIWheels::read(
  const rclcpp::Time & /*time*/, const rclcpp::Duration & /*period*/)
{
  //read wheel and IMU states

  RCLCPP_FATAL(get_logger(),"OrionVIWheels::read not implemented");
  return hardware_interface::return_type::ERROR;

  return hardware_interface::return_type::OK;
}

hardware_interface::return_type OrionVIWheels::write(
  const rclcpp::Time & /*time*/, const rclcpp::Duration & /*period*/)
{
  //send commands
  RCLCPP_FATAL(get_logger(),"OrionVIWheels::write not implemented");
   return hardware_interface::return_type::ERROR;

  return hardware_interface::return_type::OK;
}

}  // namespace orion_vi_hardware_interface

#include "pluginlib/class_list_macros.hpp"

PLUGINLIB_EXPORT_CLASS(
  orion_vi_hardware_interface::OrionVIWheels, hardware_interface::SystemInterface)
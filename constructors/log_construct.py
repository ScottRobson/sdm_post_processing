from datetime import datetime


class SignalingLog:

  def __init__(self, time, tech, layer, log_subtype, direction, channel, body):
    """
    Args:

    """
    self.time = time
    self.tech = tech
    self.layer = layer
    self.log_subtype = log_subtype
    self.direction = direction
    self.channel = channel
    self.body = body

  def __repr__(self):
    return '{} {} {} log at {}'.format(self.tech, self.layer, self.log_subtype, str(self.time))
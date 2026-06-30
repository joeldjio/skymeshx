"""Test mutual exclusion between Boids and Leader-Follower algorithms."""

import pytest


def test_boids_disables_leader_follower(qapp, swarm_ctx):
    """Enabling Boids should disable Leader-Follower."""
    # Enable Leader-Follower first
    swarm_ctx.leaderFollowerEnabled = True
    assert swarm_ctx.leaderFollowerEnabled is True
    assert swarm_ctx.boidsEnabled is False
    
    # Enable Boids - should disable Leader-Follower
    swarm_ctx.boidsEnabled = True
    assert swarm_ctx.boidsEnabled is True
    assert swarm_ctx.leaderFollowerEnabled is False


def test_leader_follower_disables_boids(qapp, swarm_ctx):
    """Enabling Leader-Follower should disable Boids."""
    # Enable Boids first
    swarm_ctx.boidsEnabled = True
    assert swarm_ctx.boidsEnabled is True
    assert swarm_ctx.leaderFollowerEnabled is False
    
    # Enable Leader-Follower - should disable Boids
    swarm_ctx.leaderFollowerEnabled = True
    assert swarm_ctx.leaderFollowerEnabled is True
    assert swarm_ctx.boidsEnabled is False


def test_disabling_does_not_trigger_mutual_exclusion(qapp, swarm_ctx):
    """Disabling one algorithm should not affect the other."""
    # Enable Leader-Follower
    swarm_ctx.leaderFollowerEnabled = True
    assert swarm_ctx.leaderFollowerEnabled is True
    
    # Disable it - should not enable Boids
    swarm_ctx.leaderFollowerEnabled = False
    assert swarm_ctx.leaderFollowerEnabled is False
    assert swarm_ctx.boidsEnabled is False


def test_consensus_compatible_with_both(qapp, swarm_ctx):
    """Consensus should be compatible with both Boids and Leader-Follower."""
    # Enable Consensus + Boids
    swarm_ctx.consensusEnabled = True
    swarm_ctx.boidsEnabled = True
    assert swarm_ctx.consensusEnabled is True
    assert swarm_ctx.boidsEnabled is True
    
    # Switch to Leader-Follower
    swarm_ctx.leaderFollowerEnabled = True
    assert swarm_ctx.consensusEnabled is True
    assert swarm_ctx.leaderFollowerEnabled is True
    assert swarm_ctx.boidsEnabled is False


def test_behavior_trees_compatible_with_all(qapp, swarm_ctx):
    """Behavior Trees should be compatible with all algorithms."""
    swarm_ctx.behaviorTreesEnabled = True
    swarm_ctx.boidsEnabled = True
    swarm_ctx.consensusEnabled = True
    
    assert swarm_ctx.behaviorTreesEnabled is True
    assert swarm_ctx.boidsEnabled is True
    assert swarm_ctx.consensusEnabled is True
    
    # Switch to Leader-Follower
    swarm_ctx.leaderFollowerEnabled = True
    assert swarm_ctx.behaviorTreesEnabled is True
    assert swarm_ctx.leaderFollowerEnabled is True
    assert swarm_ctx.consensusEnabled is True

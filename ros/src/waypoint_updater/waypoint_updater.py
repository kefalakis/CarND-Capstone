#!/usr/bin/env python

import rospy
from geometry_msgs.msg import PoseStamped
from styx_msgs.msg import Lane, Waypoint
from scipy.spatial import KDTree
import numpy as np

import math

'''
This node will publish waypoints from the car's current position to some `x` distance ahead.

As mentioned in the doc, you should ideally first implement a version which does not care
about traffic lights or obstacles.

Once you have created dbw_node, you will update this node to use the status of traffic lights too.

Please note that our simulator also provides the exact location of traffic lights and their
current status in `/vehicle/traffic_lights` message. You can use this message to build this node
as well as to verify your TL classifier.

TODO (for Yousuf and Aaron): Stopline location for each traffic light.
'''

LOOKAHEAD_WPS = 200 # Number of waypoints we will publish. You can change this number


class WaypointUpdater(object):
    def __init__(self):
        rospy.init_node('waypoint_updater')

        rospy.Subscriber('/current_pose', PoseStamped, self.pose_cb)
        rospy.Subscriber('/base_waypoints', Lane, self.waypoints_cb)

        # TODO: Add a subscriber for /traffic_waypoint and /obstacle_waypoint below


        self.final_waypoints_pub = rospy.Publisher('final_waypoints', Lane, queue_size=1)

        # TODO: Add other member variables you need below
        self.waypoint_list = []
        self.pose = None
        self.twist = None
        self.base_waypoints = None
        self.base_waypoints_tree = None
        self.waypoints_2d = None
        self.loop()


    def loop(self):
        rate = rospy.Rate(10)
        while not rospy.is_shutdown():
            if self.pose and self.base_waypoints:
                self.publish_waypoints()
            rate.sleep()

    def publish_waypoints(self):
        lane = Lane()
        current_wp_idx = self.find_closest_waypoint_idx()
        next_final_wp_idx = current_wp_idx + 200
        if(next_final_wp_idx < len(self.base_waypoints.waypoints)):
            lane.waypoints = self.base_waypoints.waypoints[current_wp_idx:next_final_wp_idx]
        #lane.header.frame_id = self.pose.header.frame_id
		#lane.header.stamp = rospy.get_rostime()
        return lane

    def find_closest_waypoint_idx(self):
        x = self.pose.position.x
        y = self.pose.position.y
        closest_idx = self.base_waypoints_tree.query([x, y], 1)[1]
        #check if closest is ahead or behind vehicle
        closest_coord = self.waypoints_2d[closest_idx]
        prev_coord = self.waypoints_2d[closest_idx-1]
        # equation for hyperplane through closest coords
        cl_vector = np.array(closest_coord)
        prev_vector = np.array(prev_coord)
        pos_vector = np.array([x, y])
        val = np.dot((cl_vector - prev_vector), (pos_vector - cl_vector))

        if  val > 0:
            closest_idx = (closest_idx + 1) % len(self.waypoints_2d)
        return closest_idx

    def pose_cb(self, msg):
        # TODO: Implement
        self.pose = msg

    def waypoints_cb(self, waypoints):
        # TODO: Implement
        self.base_waypoints = waypoints
        #print (len(self.base_waypoints))
        self.waypoints_2d = [[waypoint.pose.pose.position.x, waypoint.pose.pose.position.y]
            for waypoint in waypoints]
        #print (len(self.waypoints_2d))
        self.base_waypoints_tree = KDTree(self.waypoints_2d)
        #print (len(self.base_waypoints_tree))

    def traffic_cb(self, msg):
        # TODO: Callback for /traffic_waypoint message. Implement
        pass

    def obstacle_cb(self, msg):
        # TODO: Callback for /obstacle_waypoint message. We will implement it later
        pass

    def get_waypoint_velocity(self, waypoint):
        return waypoint.twist.twist.linear.x

    def set_waypoint_velocity(self, waypoints, waypoint, velocity):
        waypoints[waypoint].twist.twist.linear.x = velocity

    def distance(self, waypoints, wp1, wp2):
        dist = 0
        dl = lambda a, b: math.sqrt((a.x-b.x)**2 + (a.y-b.y)**2  + (a.z-b.z)**2)
        for i in range(wp1, wp2+1):
            dist += dl(waypoints[wp1].pose.pose.position, waypoints[i].pose.pose.position)
            wp1 = i
        return dist


if __name__ == '__main__':
    try:
        WaypointUpdater()
    except rospy.ROSInterruptException:
        rospy.logerr('Could not start waypoint updater node.')

from unittest import TestCase
import time
from context import AutomationContext


class TestAutomationContext(TestCase):

    def setUp(self):
        self.context = AutomationContext({})

    def test_ads_value(self):
        self.context.publishValues("test.my", {'value':123123})
        self.context.publish_queue.join()
        self.assertEqual(self.context.getValue("test.my.value"), 123123)

    def test_does_context_search_input(self):
        self.context.publishInputValues("test.my", {'value':123123})
        self.context.publish_queue.join()
        self.assertEqual(self.context.getValue("test.my.value"), 123123)
        self.assertEqual(self.context.getValue("input.test.my.value"), 123123)

    def test_does_context_search_rules(self):
        self.context.publishRuleValues("test.my", {'value':123123})
        self.context.publish_queue.join()
        self.assertEqual(self.context.getValue("test.my.value"), 123123)
        self.assertEqual(self.context.getValue("rule.test.my.value"), 123123)

    def test_does_context_search_receiver(self):
        self.context.publishReceiverValues("test.my", {'value':123123})
        self.context.publish_queue.join()
        self.assertEqual(self.context.getValue("test.my.value"), 123123)
        self.assertEqual(self.context.getValue("receiver.test.my.value"), 123123)

    def test_publishing_values_changes_state(self):
        self.assertFalse(self.context.trigger)
        self.context.publishReceiverValues("test.my", {'value':123123})
        self.context.publish_queue.join()
        self.assertTrue(self.context.trigger)

    def test_publishing_same_values_changes_no_state(self):
        self.context.publishReceiverValues("test.my", {'value':123123})
        self.context.publish_queue.join()
        self.context.trigger = False
        self.context.publishReceiverValues("test.my", {'value':123123})
        self.context.publish_queue.join()
        self.assertFalse(self.context.trigger)

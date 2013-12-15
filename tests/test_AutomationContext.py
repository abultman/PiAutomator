from unittest import TestCase
from context import AutomationContext
from mock import Mock, MagicMock


class TestAutomationContext(TestCase):

    def setUp(self):
        mock = Mock()
        mock.getSetting = MagicMock(return_value = False)
        self.context = AutomationContext(mock)
        self.context.__start_publish_queue__()

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
        self.assertTrue(self.context.trigger.qsize() == 0)
        self.context.publishReceiverValues("test.my", {'value':123123})
        self.context.publish_queue.join()
        self.assertTrue(self.context.trigger.qsize() == 1)
        self.assertTrue(self.context.trigger.get())

    def test_publishing_same_values_changes_no_state(self):
        self.context.publishReceiverValues("test.my", {'value':123123})
        self.context.publish_queue.join()
        self.assertTrue(self.context.trigger.get())
        self.context.publishReceiverValues("test.my", {'value':123123})
        self.context.publish_queue.join()
        self.assertTrue(self.context.trigger.qsize() == 0)

"""
Unit tests for course index outline.
"""
from django.test import RequestFactory
from django.urls import reverse
from rest_framework import status

from cms.djangoapps.contentstore.rest_api.v1.mixins import PermissionAccessMixin
from cms.djangoapps.contentstore.tests.utils import CourseTestCase
from cms.djangoapps.contentstore.utils import get_lms_link_for_item
from cms.djangoapps.contentstore.views.course import _course_outline_json
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.tests.factories import BlockFactory


class CourseIndexViewTest(CourseTestCase, PermissionAccessMixin):
    """
    Tests for CourseIndexView.
    """

    def setUp(self):
        super().setUp()
        with self.store.bulk_operations(self.course.id, emit_signals=False):
            self.chapter = BlockFactory.create(
                parent=self.course, display_name='Overview'
            )
            self.section = BlockFactory.create(
                parent=self.chapter, display_name='Welcome'
            )
            self.unit = BlockFactory.create(
                parent=self.section, display_name='New Unit'
            )
            self.xblock = BlockFactory.create(
                parent=self.unit,
                category='problem',
                display_name='Some problem'
            )
        self.user = UserFactory()
        self.factory = RequestFactory()
        self.request = self.factory.get(f"/course/{self.course.id}")
        self.request.user = self.user
        self.reload_course()
        self.url = reverse(
            "cms.djangoapps.contentstore:v1:course_index",
            kwargs={"course_id": self.course.id},
        )

    def test_course_index_response(self):
        """Check successful response content"""
        response = self.client.get(self.url)
        expected_response = {
            "course_release_date": "Set Date",
            "course_structure": _course_outline_json(self.request, self.course),
            "deprecated_blocks_info": {
                "deprecated_enabled_block_types": [],
                "blocks": [],
                "advance_settings_url": f"/settings/advanced/{self.course.id}"
            },
            "discussions_incontext_feedback_url": "",
            "discussions_incontext_learnmore_url": "",
            "initial_state": None,
            "initial_user_clipboard": {
                "content": None,
                "source_usage_key": "",
                "source_context_title": "",
                "source_edit_url": ""
            },
            "language_code": "en",
            "lms_link": get_lms_link_for_item(self.course.location),
            "mfe_proctored_exam_settings_url": "",
            "notification_dismiss_url": None,
            "proctoring_errors": [],
            "reindex_link": f"/course/{self.course.id}/search_reindex",
            "rerun_notification_id": None
        }

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(expected_response, response.data)

    def test_course_index_response_with_show_locators(self):
        """Check successful response content with show query param"""
        response = self.client.get(self.url, {"show": str(self.unit.location)})
        expected_response = {
            "course_release_date": "Set Date",
            "course_structure": _course_outline_json(self.request, self.course),
            "deprecated_blocks_info": {
                "deprecated_enabled_block_types": [],
                "blocks": [],
                "advance_settings_url": f"/settings/advanced/{self.course.id}"
            },
            "discussions_incontext_feedback_url": "",
            "discussions_incontext_learnmore_url": "",
            "initial_state": {
                "expanded_locators": [
                    str(self.unit.location),
                    str(self.xblock.location),
                ],
                "locator_to_show": str(self.unit.location),
            },
            "initial_user_clipboard": {
                "content": None,
                "source_usage_key": "",
                "source_context_title": "",
                "source_edit_url": ""
            },
            "language_code": "en",
            "lms_link": get_lms_link_for_item(self.course.location),
            "mfe_proctored_exam_settings_url": "",
            "notification_dismiss_url": None,
            "proctoring_errors": [],
            "reindex_link": f"/course/{self.course.id}/search_reindex",
            "rerun_notification_id": None
        }

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(expected_response, response.data)

    def test_course_index_response_with_invalid_course(self):
        """Check error response for invalid course id"""
        response = self.client.get(self.url + "1")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {
            "developer_message": f"Unknown course {self.course.id}1",
            "error_code": "course_does_not_exist"
        })

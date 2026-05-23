package com.unutrip

import androidx.test.ext.junit.rules.ActivityScenarioRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.unutrip.ui.auth.AuthActivity
import org.junit.Assert.assertNotNull
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class AuthFlowInstrumentedTest {

    @get:Rule
    val activityRule = ActivityScenarioRule(AuthActivity::class.java)

    @Test
    fun authActivity_launches() {
        activityRule.scenario.onActivity { activity ->
            assertNotNull(activity.findViewById(R.id.etEmail))
        }
    }
}

